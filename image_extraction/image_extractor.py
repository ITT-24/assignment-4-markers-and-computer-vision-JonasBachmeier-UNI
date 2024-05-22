import cv2
import numpy as np
import sys

WINDOW_NAME = "Image Extractor"

# Load image
if len(sys.argv) < 7:
    print("not enough arguments")
    print("Usage: python image_extractor.py <image_path> <output_path> <height> <width> <result_width> <result_height>")
    sys.exit(1)

img = cv2.imread(sys.argv[1])
if img is None:
    print("image not found")
    sys.exit(1)

height = int(sys.argv[3])
width = int(sys.argv[4])

img = cv2.resize(img, (width, height))

result_width = int(sys.argv[5])
result_height = int(sys.argv[6])

img_copy = img.copy()

points = []

def set_points(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            points.append((x, y))
            cv2.circle(img_copy, (x, y), 5, (0, 0, 255), -1)
            cv2.imshow(WINDOW_NAME, img_copy)

def sort_points(points):
    center = [sum(point[0] for point in points)/len(points), sum(point[1] for point in points)/len(points)]
    
    sorted_points = sorted(points, key=lambda point: np.arctan2(point[1]-center[1], point[0]-center[0]))

    return sorted_points

def transform_image(points, img):
    points = sort_points(points)

    pts1 = np.float32(points)
    pts2 = np.float32([[0, 0], [result_width, 0], [result_width, result_height], [0, result_height]])

    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    result = cv2.warpPerspective(img, matrix, (result_width, result_height), flags=cv2.INTER_LINEAR)

    return result

cv2.namedWindow(WINDOW_NAME)
cv2.setMouseCallback(WINDOW_NAME, set_points)

while True:
    cv2.imshow(WINDOW_NAME, img_copy)

    key = cv2.waitKey(1) & 0xFF
    # calls the transformation function and saves the image if 4 points have been selected
    if len(points) == 4:
        if key == ord('s'):
            result = transform_image(points, img)
            cv2.imwrite(sys.argv[2], result)
            break
    
    # resets the points and the image when esc is pressed (27 is the ascii value for esc)
    if key == 27:
        points = []
        img_copy = img.copy()

