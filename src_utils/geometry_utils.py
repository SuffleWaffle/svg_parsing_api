import numpy as np
def center_coord(line):
    return (line[0] + line[2]) // 2, (line[1] + line[3]) // 2

def euclidean_dist(point1, point2):
    x0, y0 = point1
    x1, y1 = point2
    return np.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)