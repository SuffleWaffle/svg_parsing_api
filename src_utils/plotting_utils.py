import numpy as np
import cv2


def plot_lines_on_image(lines, width, height):
    # Create a white background image
    img = np.zeros((height, width, 3), np.uint8)
    img.fill(255)

    # Plot lines on the image
    for line in lines:
        x1, y1, x2, y2 = line
        cv2.line(img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 1)

    return img
