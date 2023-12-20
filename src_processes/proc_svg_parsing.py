# >>>> </> STANDARD IMPORTS </>
# >>>> ********************************************************************************
import logging
# >>>> ********************************************************************************

# >>>> </> EXTERNAL IMPORTS </>
# >>>> ********************************************************************************
# import numpy as np
# from fastapi import UploadFile
# >>>> ********************************************************************************

# >>>> </> LOCAL IMPORTS </>
# >>>> ********************************************************************************
from src_logging import log_config

# from src_utils.svg_parsing import extract_lines, extract_svg_elements, rgb_to_hex
from src_utils.svg_parsing import SVGExtract
from src_utils.svg_parsing import SVGLines, SVGCircles, SVGRectangles, SVGCubBezier, SVGQuadBezier
from src_utils.loading_utils import load_pdf
from fastapi import HTTPException, status
# >>>> ********************************************************************************

# ________________________________________________________________________________
# --- INITIAL CONFIG - LOGGER SETUP ---
logger = log_config.setup_logger(logger_name=__name__, logging_level=logging.INFO)


def change_attributes(attributes):
    for i in attributes:
        try:
            i['color'] = SVGExtract.rgb_to_hex(i.get('color'))
            i['fill'] = SVGExtract.rgb_to_hex(i.get('fill'))
            del i['rect']
        except Exception as e:
            pass

    return attributes


# ________________________________________________________________________________
class SVGParser:
    # ________________________________________________________________________________
    @staticmethod
    def get_file_data(pdf_file_obj, page_num: int = 0, s3_origin: bool = False):
        logger.info(">>> 1 - LOADING PDF FILE")

        pdf_doc, doc_page, _, pdf_size = load_pdf(pdf_file_obj=pdf_file_obj,
                                                  page_num=page_num,
                                                  s3_origin=s3_origin)

        logger.info(">>> 2 - EXTRACTING SVG ELEMENTS FROM PDF PAGE")

        svg_elements = SVGExtract.extract_svg_elements(doc_page=doc_page)

        if not svg_elements:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="No svg elements found")

        return pdf_doc, doc_page, pdf_size, svg_elements

    # ________________________________________________________________________________
    @classmethod
    def extract_svg_lines(cls, pdf_file_obj, page_num: int = 0,
                          round_threshold: float = 0.2, s3_origin: bool = False):
        pdf_doc, doc_page, pdf_size, svg_elements = cls.get_file_data(pdf_file_obj=pdf_file_obj,
                                                                      page_num=page_num,
                                                                      s3_origin=s3_origin)
        width, height = pdf_size

        logger.info(">>> 3.1 - STARTED PARSING -> SVG LINES")

        lines, attributes = SVGLines(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                   doc_page,
                                                                                   doc_page.rotation_matrix)

        logger.info(">>> 3.2 - STARTED PARSING -> SVG LINES ATTRIBUTES")

        # TODO: change to extraction of all attributes + Rect to list
        attributes = change_attributes(attributes)

        logger.info(">>> 4 - RETURN -> LINES AND ATTRIBUTES DATA")

        return lines, width, height, attributes

    # ________________________________________________________________________________
    @classmethod
    def extract_svg_circles(cls, pdf_file_obj, page_num: int = 0,
                            round_threshold: float = 0.2, s3_origin: bool = False):
        pdf_doc, doc_page, pdf_size, svg_elements = cls.get_file_data(pdf_file_obj=pdf_file_obj,
                                                                      page_num=page_num,
                                                                      s3_origin=s3_origin)
        width, height = pdf_size

        logger.info(">>> 3.1 - STARTED PARSING -> SVG CIRCLES")

        circles_data, attributes = SVGCircles(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                            doc_page,
                                                                                            doc_page.rotation_matrix)

        logger.info(">>> 3.2 - STARTED PARSING -> SVG CIRCLES ATTRIBUTES")

        # TODO: change to extraction of all attributes + Rect to list
        attr_data = change_attributes(attributes)

        logger.info(">>> 4 - RETURN -> CIRCLES DATA")

        return circles_data, width, height, attr_data

    # ________________________________________________________________________________
    @classmethod
    def extract_svg_rectangles(cls, pdf_file_obj, page_num: int = 0,
                               round_threshold: float = 0.2, s3_origin: bool = False):
        pdf_doc, doc_page, pdf_size, svg_elements = cls.get_file_data(pdf_file_obj=pdf_file_obj,
                                                                      page_num=page_num,
                                                                      s3_origin=s3_origin)
        width, height = pdf_size

        logger.info(">>> 3.1 - STARTED PARSING -> SVG RECTANGLES")

        rectangles_data, attributes = SVGRectangles(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                                  doc_page,
                                                                                                  doc_page.rotation_matrix)

        logger.info(">>> 3.2 - STARTED PARSING -> SVG RECTANGLES ATTRIBUTES")

        # TODO: change to extraction of all attributes + Rect to list
        attr_data = change_attributes(attributes)

        logger.info(">>> 4 - RETURN -> RECTANGLES DATA")

        return rectangles_data, width, height, attr_data

    # ________________________________________________________________________________
    @classmethod
    def extract_svg_cub_bezier_lines(cls, pdf_file_obj, config: dict, page_num: int = 0,
                                     round_threshold: float = 0.2, s3_origin: bool = False):
        pdf_doc, doc_page, pdf_size, svg_elements = cls.get_file_data(pdf_file_obj=pdf_file_obj,
                                                                      page_num=page_num,
                                                                      s3_origin=s3_origin)
        width, height = pdf_size

        logger.info(">>> 3.1 - STARTED SVG PARSING -> SVG CUB BEZIER LINES")

        cub_bezier_data, attributes = SVGCubBezier(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                                 doc_page,
                                                                                                 doc_page.rotation_matrix,
                                                                                                 **config["extract_svg_cub_bezier_lines"])

        logger.info(">>> 3.2 - STARTED PARSING -> SVG CUB BEZIER LINES ATTRIBUTES")

        # TODO: change to extraction of all attributes + Rect to list
        attr_data = change_attributes(attributes)

        logger.info(">>> 4 - RETURN -> CUB BEZIER LINES DATA")

        return cub_bezier_data, width, height, attr_data

    # ________________________________________________________________________________
    @classmethod
    def extract_svg_quad_bezier_lines(cls, pdf_file_obj, page_num: int = 0,
                                      round_threshold: float = 0.2, s3_origin: bool = False):
        pdf_doc, doc_page, pdf_size, svg_elements = cls.get_file_data(pdf_file_obj=pdf_file_obj,
                                                                      page_num=page_num,
                                                                      s3_origin=s3_origin)
        width, height = pdf_size

        logger.info(">>> 3.1 - STARTED PARSING -> SVG QUAD BEZIER LINES")

        quad_bezier_data, attributes = SVGQuadBezier(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                                   doc_page,
                                                                                                   doc_page.rotation_matrix)

        logger.info(">>> 3.2 - STARTED PARSING -> SVG QUAD BEZIER LINES ATTRIBUTES")

        # TODO: change to extraction of all attributes + Rect to list
        attr_data = change_attributes(attributes)

        logger.info(">>> 4 - RETURN -> QUAD BEZIER LINES DATA")

        return quad_bezier_data, width, height, attr_data

    @classmethod
    def extract_all_svg(cls, pdf_file_obj, config: dict, page_num: int = 0,
                        round_threshold=0.2, s3_origin: bool = False):
        # get pdf file
        pdf_doc, doc_page, pdf_size, svg_elements = cls.get_file_data(pdf_file_obj=pdf_file_obj,
                                                                      page_num=page_num,
                                                                      s3_origin=s3_origin)
        width, height = pdf_size

        all_svg = {}

        logger.info(">>> 3.1 - STARTED PARSING -> SVG LINES")
        lines, attributes = SVGLines(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                   doc_page,
                                                                                   doc_page.rotation_matrix)

        attr_data = change_attributes(attributes)

        all_svg["lines"] = {"lines_data": lines,
                            "lines_attributes": attr_data,
                            "svg_width": width,
                            "svg_height": height}

        logger.info(">>> 3.2 - STARTED PARSING -> SVG CUBIC LINES")
        cub_bezier_data, attributes = SVGCubBezier(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                                 doc_page,
                                                                                                 doc_page.rotation_matrix,
                                                                                                 **config["extract_svg_cub_bezier_lines"])

        attr_data = change_attributes(attributes)

        all_svg["cubic_lines"] = {"cub_bezier_lines_data": cub_bezier_data,
                                  "attributes": attr_data,
                                  "svg_width": width,
                                  "svg_height": height}

        logger.info(">>> 3.3 - STARTED PARSING -> SVG QUADS")
        quad_bezier_data, attributes = SVGQuadBezier(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                                   doc_page,
                                                                                                   doc_page.rotation_matrix)
        attr_data = change_attributes(attributes)

        all_svg["quads"] = {"quad_bezier_lines_data": quad_bezier_data,
                            "attributes": attr_data,
                            "svg_width": width,
                            "svg_height": height}

        logger.info(">>> 3.4 - STARTED PARSING -> SVG CIRCLES")
        circles_data, attributes = SVGCircles(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                            doc_page,
                                                                                            doc_page.rotation_matrix)

        attr_data = change_attributes(attributes)

        all_svg["circles"] = {"circles_data": circles_data,
                              "attributes": attr_data,
                              "svg_width": width,
                              "svg_height": height}

        logger.info(">>> 3.5 - STARTED PARSING -> SVG RECTANGLES")
        rectangles_data, attributes = SVGRectangles(round_threshold=round_threshold).extract_data(svg_elements,
                                                                                                  doc_page,
                                                                                                  doc_page.rotation_matrix)

        attr_data = change_attributes(attributes)

        all_svg['rectangles'] = {"rectangles_data": rectangles_data,
                                 "attributes": attr_data,
                                 "svg_width": width,
                                 "svg_height": height}

        return all_svg
