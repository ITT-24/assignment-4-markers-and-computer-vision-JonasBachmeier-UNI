# Create a program called AR-game.py. The program should read out your webcam
# image. Use a board with an AruCo marker in each corner, extract the region bet-
# ween the markers, and transform it to a rectangle with the resolution of your
# webcam. Keep in mind that not all webcams have the same resolution! Display
# the extracted and warped rectangle in a pyglet application. Now, add some game
# mechanics based on the image in the extracted rectangle. For example, players
# could be able to use their finger to destroy targets or to move things around.
# Score
# (2P) The region of interest is detected, extracted, transformed, and displayed.
# (4P) Objects (such as fingers) in the region of interest are tracked reliably and
# interaction with game objects works.
# (2P) Game mechanics work and (kind of) make sense.
# (1P) Performance is ok.
# (1P) The program does not crash.

import cv2
import cv2.aruco as aruco
import sys
import numpy as np
import pyglet as pg


video_id = 0

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

# Create a video capture object for the webcam
cap = cv2.VideoCapture(video_id)

# get webcam resolution
ret, frame = cap.read()
height, width, _ = frame.shape

# aruco setup
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
aruco_params = aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

# pyglet window
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
window = pg.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

def sort_points(points):
    # Calculate the centroid of the points
    centroid = [sum(point[0] for point in points)/len(points), sum(point[1] for point in points)/len(points)]
    
    # Sort points based on their angle with respect to the centroid
    sorted_points = sorted(points, key=lambda point: -np.arctan2(point[1]-centroid[1], point[0]-centroid[0]))
    
    # Reorder the points to match the order expected by cv2.getPerspectiveTransform
    sorted_points = sorted_points[3:] + sorted_points[:3]

    return sorted_points

def transform_image(points, img):
    sorted_points = sort_points(points)
    print(sorted_points)
    pts1 = np.float32(sorted_points)
    pts2 = np.float32([[0, 0], [WINDOW_WIDTH, 0], [WINDOW_WIDTH, WINDOW_HEIGHT], [0, WINDOW_HEIGHT]])

    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    result = cv2.warpPerspective(img, matrix, (WINDOW_WIDTH, WINDOW_HEIGHT), flags=cv2.INTER_LINEAR)

    return result

@window.event
def on_draw():
    window.clear()
    ret, frame = cap.read()
    # detect aruco markers
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = detector.detectMarkers(gray)
    marker_points = []
    if ids is not None:
        #print(ids)
        # Draw lines along the sides of the marker
        aruco.drawDetectedMarkers(frame, corners)
        # turn corners into center point
        # (array([[[521., 196.], [522.,  99.], [628., 103.], [626., 203.]]], dtype=float32),)
        #print(corners[0][0][0][0])
        for i in range(len(ids)):
           # print(i)
            center_x = (corners[i][0][0][0] + corners[i][0][1][0] + corners[i][0][2][0] + corners[i][0][3][0]) / 4
            center_y = (corners[i][0][0][1] + corners[i][0][1][1] + corners[i][0][2][1] + corners[i][0][3][1]) / 4
            marker_point = (int(center_x), int(center_y))
            print(marker_point)
            marker_points.append(marker_point)
            pg.text.Label(text=str(ids[i]), anchor_x='center', x=marker_point[0], y=marker_point[1], color=(255, 0, 0, 255)).draw()
        
        if len(ids) == 4:
            print(ids)
            # extract region of interest
            result = transform_image(marker_points, frame)
            # display result
            img = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            img = cv2.flip(img, 0)
            img = cv2.flip(img, 1)
            pg.sprite.Sprite(pg.image.ImageData(width=WINDOW_WIDTH, height=WINDOW_HEIGHT, fmt='RGB', data=img.tobytes())).draw()
            
        
    # # prep frame for pyglet
    # img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # img = cv2.flip(img, 0)
    # img = cv2.flip(img, 1)

    # pg.sprite.Sprite(pg.image.ImageData(width=width, height=height, fmt='RGB', data=img.tobytes())).draw()
    

pg.app.run()