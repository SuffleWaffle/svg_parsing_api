# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import logging
from itertools import chain
import math

import fitz

from src_utils.geometry_utils import *
# from typing import List, Tuple, Dict, Union
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
import numpy as np
from abc import abstractmethod
# >>>> ********************************************************************************

# >>>> </> LOCAL IMPORTS </>
# >>>> ********************************************************************************
from src_logging import log_config
# >>>> ********************************************************************************

# ________________________________________________________________________________
# --- INITIAL CONFIG - LOGGER SETUP ---
logger = log_config.setup_logger(__name__, logging_level=logging.INFO)



def fitz_to_json(svg_elements):
    def _fitz_to_list(obj):
        if isinstance(obj, (fitz.Rect, fitz.Point)):
            obj = list(obj)
        if isinstance(obj, fitz.Quad):
            obj = list(map(list, obj))

        return obj

    for i in svg_elements:
        i['items'] = [[_fitz_to_list(z) for z in j] \
                      for j in i['items']]
        i['rect'] = list(i['rect'])
    return svg_elements

def json_to_fitz(svg_elements):
    def _list_to_fitz(list_object, object_type):
        if object_type=='re':
            list_object = fitz.Rect(*list_object)
        if object_type in ['l', 'c']:
            list_object = fitz.Point(*list_object)
        if object_type=='qu':
            list_object = fitz.Quad(list(map(lambda x: fitz.Point(*x), list_object)))
        return list_object

    for i in svg_elements:
        i['items'] = [[j[0]]+[_list_to_fitz(z, j[0]) if isinstance(z, list) else z for z in j[1:]] \
                      for j in i['items']]
        i['rect'] = fitz.Rect(*i['rect'])

    return svg_elements


class SVGExtract:
    ROUND_THRESHOLD = 0.2

    def __init__(self, round_threshold=None):
        SVGExtract.ROUND_THRESHOLD = round_threshold if round_threshold \
            else SVGExtract.ROUND_THRESHOLD

    @staticmethod
    def extract_svg_elements(doc_page):
        return doc_page.get_drawings()

    @staticmethod
    def rgb_to_hex(rgb):
        # Convert RGB values (0-1) to hexadecimal format (#RRGGBB)
        if rgb:
            r, g, b = [int(val * 255) for val in rgb]
            hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
            return hex_color
        return rgb

    @staticmethod
    def bezier(t, points):
        if len(points) == 1:
            return points[0]
        return (1 - t) * SVGExtract.bezier(t, points[:-1]) + t * SVGExtract.bezier(t, points[1:])

    @staticmethod
    def round(number):
        number = np.round(number, 1)
        string_number = str(number)
        float_part = int(string_number.split('.')[-1])
        if float_part >= 5:
            return int(number) + 1
        else:
            return int(number)

    @staticmethod
    def round_line(line, thr=0.1):
        x1, y1, x2, y2 = line
        rounded_x1, rounded_y1, rounded_x2, rounded_y2 = (SVGExtract.round(x1), SVGExtract.round(y1),
                                                          SVGExtract.round(x2), SVGExtract.round(y2))
        if abs(y1 - y2) < thr:
            rounded_y1 = max(rounded_y1, rounded_y2)
            rounded_y2 = rounded_y1

        if abs(x1 - x2) < thr:
            rounded_x1 = max(rounded_x1, rounded_x2)
            rounded_x2 = rounded_x1
        return rounded_x1, rounded_y1, rounded_x2, rounded_y2

    @staticmethod
    def vectorized_round(numbers):
        numbers = np.round(numbers, 1)
        float_part, int_part = np.modf(numbers)
        to_add = (float_part >= 0.5).astype(int)
        rounded = int_part + to_add
        return rounded.astype(int).tolist()

    @staticmethod
    def vectorized_round_line(lines, thr=0.1):
        lines = np.array(lines)
        rounded = SVGExtract.vectorized_round(lines)
        rounded = np.array(rounded)

        mask_y = np.abs(lines[:, 1] - lines[:, 3]) < thr
        max_y = rounded[mask_y][:, [1, 3]].max(axis=1)
        rounded[mask_y, 1] = max_y
        rounded[mask_y, 3] = max_y

        mask_x = np.abs(lines[:, 0] - lines[:, 2]) < 0.1
        max_x = rounded[mask_x][:, [0, 2]].max(axis=1)
        rounded[mask_x, 0] = max_x
        rounded[mask_x, 2] = max_x

        return rounded.astype(int).tolist()


    @abstractmethod
    def extract_data(cls, svg_elements, rotation, rotation_matrix):
        """
        Extracts data in the form of geometric primitives
        """
        pass


class SVGLines(SVGExtract):
    @classmethod
    def extract_data(cls, svg_elements, rotation, rotation_matrix):
        svg_elements = json_to_fitz(svg_elements)
        # Extract lines from SVG elements
        lines = []
        attributes = []
        for group_id, i in enumerate(svg_elements):
            tmp_lines = []
            for j in i["items"]:
                if j[0] == "l":
                    tmp_lines.append(j[1:])
            tmp_attributes = dict([(k, v) for k, v in i.items() if k != "items"])
            tmp_attributes['group_id'] = group_id
            if tmp_lines:
                if tmp_attributes['closePath']:
                    tmp_lines.append((tmp_lines[0][0], tmp_lines[-1][-1]))
                lines.extend(tmp_lines)
                attributes.extend([tmp_attributes for _ in range(len(tmp_lines))])

        if not lines:
            logger.error("EXCEPTION -> No Lines found in the SVG elements.")

        if rotation:
            lines = [[fitz_line_points[0] * rotation_matrix, fitz_line_points[1] * rotation_matrix]
                     for fitz_line_points in lines]

        lines = [[i[0].x, i[0].y, i[1].x, i[1].y] for i in lines]
        lines = cls.vectorized_round_line(lines)
        lines = list(map(tuple, lines))

        return lines, attributes

    # get rid of outliers for now
    @staticmethod
    def filter_lines_by_size_and_bounds(lines, img_width, img_height):
        filtered_lines = []
        to_leave = []
        for c, (x1, y1, x2, y2) in enumerate(lines):
            # Check if both endpoints of the line are within the bounds of the image
            if (0 <= x1 < img_width and
                    0 <= y1 < img_height and
                    0 <= x2 < img_width and
                    0 <= y2 < img_height):
                filtered_lines.append((x1, y1, x2, y2))
                to_leave.append(c)
        return filtered_lines, to_leave


class SVGCircles(SVGExtract):
    @classmethod
    def extract_data(cls, svg_elements, rotation, rotation_matrix):
        svg_elements = json_to_fitz(svg_elements)
        # --- Extracting circles data
        cubics: list = []
        attributes: list = []

        for group_id, svg_element in enumerate(svg_elements):
            for item in svg_element["items"]:
                if item[0] == "c":
                    to_add = svg_element["items"]
                    to_add = [i[1:] for i in to_add if i[0] == 'c']
                    if rotation:
                        to_add = [[j * rotation_matrix for j in i] for i in to_add]
                    cubics.append(to_add)
                    tmp_attributes = dict([(key, val) for key, val in svg_element.items() if key != "items"])
                    tmp_attributes['group_id'] = group_id
                    attributes.append(tmp_attributes)
                    break

        # ________________________________________________________________________________
        cubics = [[list(map(list, j)) for j in i] for i in cubics]
        cubics = [[[list(chain(*j[c:c + 2])) for c in range(len(j) - 1)] for j in i] for i in cubics]

        for_circles: list = []
        filtered_attributes: list = []
        for idx, c in enumerate(cubics):
            if len(c) == 4:
                for_circles.append(c)
                filtered_attributes.append(attributes[idx])

        # ________________________________________________________________________________
        circles_data: list = []
        circles_attributes: list = []
        for idx, i in enumerate(for_circles):
            lines_in_cubic = list(chain(*i))

            horizontal_lines = [j for j in lines_in_cubic if j[1] == j[3]]
            vertical_lines = [j for j in lines_in_cubic if j[0] == j[2]]

            other_lines = [j for j in lines_in_cubic if j[0] != j[2] and j[1] != j[3]]
            if len(horizontal_lines) == len(vertical_lines):
                other_centers = [center_coord(i) for i in other_lines]
                # TODO: Rework circle center detection and circle parsing in general
                try:
                    center1 = other_centers[0]
                    diameter, center2 = max([(math.dist(center1, i), i) for i in other_centers[1:]],
                                            key=lambda x: x[0])
                    center = (center1[0] + center2[0]) // 2, (center1[1] + center2[1]) // 2
                    circles_data.append([center, diameter // 2, lines_in_cubic])
                    circles_attributes.append(filtered_attributes[idx])
                except Exception as e:
                    logger.error(f'Got exception : {str(e)}')
                    continue

        if not circles_data:
            logger.error("ERROR -> No quad beizer found in the SVG elements.")

        # ________________________________________________________________________________
        # --- Using list comprehension to convert the data and convert float to int
        x_center = cls.vectorized_round([circle[0][0] for circle in circles_data])
        y_center = cls.vectorized_round([circle[0][1] for circle in circles_data])
        radius = cls.vectorized_round([circle[1] for circle in circles_data])

        circles_data_dicts = [{"center": {"x": x_center[c],
                                          "y": y_center[c]},
                               "radius": radius[c],
                               "lines": cls.vectorized_round_line(circle[2])}
                              for c, circle in enumerate(circles_data)]

        return circles_data_dicts, circles_attributes


class SVGRectangles(SVGExtract):
    @classmethod
    def extract_data(cls, svg_elements, rotation, rotation_matrix):
        svg_elements = json_to_fitz(svg_elements)
        # --- Extracting rectangles data
        rectangles_data: list = []
        attributes: list = []

        for group_id, svg_element in enumerate(svg_elements):
            for item in svg_element["items"]:
                if item[0] == "re":
                    rectangles_data.append(item[1])
                    tmp_attributes = dict([(key, val) for key, val in svg_element.items() if key != "items"])
                    tmp_attributes['group_id'] = group_id
                    attributes.append(tmp_attributes)
                    break

        # ________________________________________________________________________________
        if not rectangles_data:
            logger.error("ERROR -> No Rectangles found in the SVG elements.")

        # ________________________________________________________________________________
        if rotation:
            rectangles_data = [fitz_rect * rotation_matrix for fitz_rect in rectangles_data]

        # ________________________________________________________________________________
        # --- Using list comprehension to convert the data and convert float to int
        rectangles_data = [[fitz_rect.x0, fitz_rect.y0, fitz_rect.x1, fitz_rect.y1]
        for fitz_rect in rectangles_data]
        rectangles_data = cls.vectorized_round(rectangles_data)

        return rectangles_data, attributes


class SVGCubBezier(SVGExtract):
    @classmethod
    def extract_data(cls, svg_elements, rotation, rotation_matrix,
                     interpolation_t=50):
        svg_elements = json_to_fitz(svg_elements)
        # --- Extracting cub Bezier Points data
        cub_bezier_points_data: list = []
        attributes: list = []

        for group_id, svg_element in enumerate(svg_elements):
            for item in svg_element["items"]:
                if item[0] == "c":
                    to_add = svg_element["items"]
                    to_add = [i[1:] for i in to_add if i[0] == "c"]
                    if rotation:
                        to_add = [[j * rotation_matrix for j in i] for i in to_add]
                    cub_bezier_points_data.append(to_add)
                    tmp_attributes = dict([(key, val) for key, val in svg_element.items() if key != "items"])
                    tmp_attributes['group_id'] = group_id
                    attributes.append(tmp_attributes)
                    break

        if not cub_bezier_points_data:
            logger.error("ERROR -> No cubic bezier points found in the SVG elements.")

        cub_bezier_points_data = [[[(z.x, z.y) for z in j] for j in i] for i in cub_bezier_points_data]
        cub_bezier_lines_data: list = []
        new_attributes: list = []

        for c, ent in enumerate(cub_bezier_points_data):
            if len(ent) != 4:
                tmp = []
                for points in ent:
                    approximation = [list(cls.bezier(i, np.array(points))) for i in np.linspace(0, 1, interpolation_t)]
                    tmp.extend([list(chain(*approximation[i:i + 2])) for i in range(len(approximation) - 1)])
                new_attributes.extend([attributes[c] for _ in range(len(tmp))])
                cub_bezier_lines_data.extend(tmp)
        if cub_bezier_lines_data:
            cub_bezier_lines_data = cls.vectorized_round(cub_bezier_lines_data)
        return cub_bezier_lines_data, new_attributes


class SVGQuadBezier(SVGExtract):
    @classmethod
    def extract_data(cls, svg_elements, rotation, rotation_matrix):
        svg_elements = json_to_fitz(svg_elements)
        # --- Extracting quad Bezier Points data
        quad_bezier_lines_data: list = []
        attributes: list = []

        for group_id, svg_element in enumerate(svg_elements):
            for item in svg_element["items"]:
                if item[0] == "qu":
                    to_add = svg_element["items"]
                    to_add = [i[1] for i in to_add if i[0] == "qu"]
                    if rotation:
                        to_add = [[j * rotation_matrix for j in i] for i in to_add]
                    quad_bezier_lines_data.append(to_add)
                    tmp_attributes = dict([(key, val) for key, val in svg_element.items() if key != "items"])
                    tmp_attributes['group_id'] = group_id
                    attributes.append(tmp_attributes)
                    break

        if not quad_bezier_lines_data:
            logger.error("ERROR -> No quad beizer found in the SVG elements.")

        quad_bezier_lines_data = [[[(z.x, z.y) for z in j] for j in i] for i in quad_bezier_lines_data]

        new_attributes: list = []
        for c, i in enumerate(quad_bezier_lines_data):
            if len(i) == 1:
                new_attributes.append(attributes[c])
            else:
                new_attributes.extend([attributes[c] for _ in range(len(i))])

        quad_bezier_lines_data = list(chain(*quad_bezier_lines_data))

        quads_data: list = []

        for c, i in enumerate(quad_bezier_lines_data):
            ul, ur, ll, lr = i

            quads_lines = [(*ul, *ur), (*ll, *ul), (*lr, *ur), (*ll, *lr)]
            quads_lines = cls.vectorized_round_line(quads_lines)
            xs = [j[0] for j in quads_lines]
            ys = [j[1] for j in quads_lines]
            quads_data.append({'bbox': {'x_min': min(xs), 'y_min': min(ys), 'x_max': max(xs), 'y_max': max(ys)},
                               'lines': quads_lines
                               })

        return quads_data, new_attributes
