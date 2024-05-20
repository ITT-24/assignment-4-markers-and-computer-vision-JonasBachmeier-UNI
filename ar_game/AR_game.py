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
import random

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

# Constants
BALL_SPEED = 10
BALL_SIZE = 20
SPEED_UP = 1.1
START_SPEED = 1

# calculated the center of all point and then sorts them by the angle between the center and the point
def sort_points(points):
    center = [sum(point[0] for point in points)/len(points), sum(point[1] for point in points)/len(points)]
    
    sorted_points = sorted(points, key=lambda point: np.arctan2(point[1]-center[1], point[0]-center[0]), reverse=True)

    return sorted_points

def transform_image(points, img):
    sorted_points = sort_points(points)
    pts1 = np.float32(sorted_points)
    pts2 = np.float32([[0, 0], [WINDOW_WIDTH, 0], [WINDOW_WIDTH, WINDOW_HEIGHT], [0, WINDOW_HEIGHT]])

    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    result = cv2.warpPerspective(img, matrix, (WINDOW_WIDTH, WINDOW_HEIGHT), flags=cv2.INTER_LINEAR)

    result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)

    result = cv2.flip(result, 1)

    return result

def prepare_player_object(img):
    # convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # smooth the image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)


    # threshold
    threshold = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    #threshold = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # perform opening and another erosion
    kernel = np.ones((5, 5), np.uint8)
    closing = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel, iterations=2)
    dilate = cv2.dilate(closing, kernel, iterations=1)

    # turn image back to 3 channels
    dilate = cv2.cvtColor(dilate, cv2.COLOR_GRAY2RGB)

    return dilate

def prepare_field(img):

    # create a red rectangle from top to bttom in the middle of the image with width of 1/3 of the image
    img[0:WINDOW_HEIGHT, WINDOW_WIDTH//3:WINDOW_WIDTH*2//3] = [255, 0, 0]

    return img

class Ball:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.shape = pg.shapes.Circle(x, y, radius, color=(0, 0, 255))
        self.dir = [random.choice([-BALL_SPEED, BALL_SPEED]), random.choice([-BALL_SPEED, BALL_SPEED])]
        self.is_colliding = False
        self.has_crossed = False
        self.side = None
        self.can_change_direction = True
        self.score = 0	
        self.speed = START_SPEED


    def draw(self):
        self.shape.draw()
    
    def move(self):
        self.shape.x += int(self.dir[0] * self.speed)
        self.shape.y += int(self.dir[1] * self.speed)
        if self.shape.x > WINDOW_WIDTH or self.shape.x < 0:
            self.respawn()
        if self.shape.y > WINDOW_HEIGHT or self.shape.y < 0:
            self.dir[1] *= -1

        # check if the ball has crossed the center line and reset the flag to allow changing direction
        if not self.can_change_direction and self.side != self.check_ball_side():
            self.can_change_direction = True
        self.side = self.check_ball_side()
    
    def respawn(self):
        self.dir = [random.choice([-BALL_SPEED, BALL_SPEED]), random.choice([-BALL_SPEED, BALL_SPEED])]
        self.shape.x = WINDOW_WIDTH//2
        self.shape.y = WINDOW_HEIGHT//2
        self.score = 0
        self.speed = START_SPEED
        pg.shapes.Rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, color=(255, 0, 0)).draw()
    
    def check_collision(self, player):
        # safety check to prevent index out of bounds
        if self.shape.x >= player.shape[1]:
            self.shape.x = player.shape[1] - 1
        if self.shape.y >= player.shape[0]:
            self.shape.y = player.shape[0] - 1

        if not self.is_colliding and np.array_equal(player[self.shape.y, self.shape.x], [255, 255, 255]):
            self.is_colliding = True
        #elif player[self.shape.y, self.shape.x] == [0, 0, 0] or player[self.shape.y, self.shape.x] == [255, 0, 0]:
        else:
            self.is_colliding = False
        return self.is_colliding
    
    def change_direction(self):
        if self.is_colliding and self.can_change_direction:
            self.dir[0] *= -1
            self.can_change_direction = False
            self.score += 1
            self.speed *= SPEED_UP

    def check_ball_side(self):
        if self.shape.x > WINDOW_WIDTH / 2:
            return 'right'
        else:
            return 'left'

# The last frame where all 4 markers were detected should be remembered so its drawn when the markers are not detected
last_sprite = None
ball = Ball(WINDOW_WIDTH//2, WINDOW_HEIGHT//2, BALL_SIZE)

game_started = False

@window.event
def on_key_press(symbol, modifiers):
    global game_started
    if symbol == pg.window.key.SPACE:
        game_started = not game_started

@window.event
def on_draw():
    global ball
    global last_sprite
    global game_started
    if not game_started:
        pg.text.Label(text="Hands-Pong",font_size=25 , x=WINDOW_WIDTH//2, y=WINDOW_HEIGHT//2 + 80, anchor_x='center').draw()
        pg.text.Label(text="Use your Hands to bounce ball back to the other side", x=WINDOW_WIDTH//2, y=WINDOW_HEIGHT//2 + 40, anchor_x='center').draw()
        pg.text.Label(text="Every bounce you get 1 point and the ball gains speed", x=WINDOW_WIDTH//2, y=WINDOW_HEIGHT//2 + 20, anchor_x='center').draw()
        pg.text.Label(text="When the ball reaches one of the sides, the game gets reset", x=WINDOW_WIDTH//2, y=WINDOW_HEIGHT//2, anchor_x='center').draw()
        
        pg.text.Label(text="Press SPACE to start or pause the game", x=WINDOW_WIDTH//2, y=WINDOW_HEIGHT//2 - 50, anchor_x='center').draw()
    else:
        window.clear()
        ret, frame = cap.read()
        # detect aruco markers
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejectedImgPoints = detector.detectMarkers(gray)
        marker_points = []
        if last_sprite is not None:
            last_sprite.draw()
        if ids is not None:
            for i in range(len(ids)):
                center_x = (corners[i][0][0][0] + corners[i][0][1][0] + corners[i][0][2][0] + corners[i][0][3][0]) / 4
                center_y = (corners[i][0][0][1] + corners[i][0][1][1] + corners[i][0][2][1] + corners[i][0][3][1]) / 4
                marker_point = (int(center_x), int(center_y))
                marker_points.append(marker_point)
                pg.text.Label(text=str(ids[i]), anchor_x='center', x=marker_point[0], y=marker_point[1], color=(255, 0, 0, 255)).draw()
            
            if len(ids) == 4:

                # extract region of interest
                img = transform_image(marker_points, frame)

                last_sprite = pg.sprite.Sprite(pg.image.ImageData(width=WINDOW_WIDTH, height=WINDOW_HEIGHT, fmt='RGB', data=img.tobytes()))
                last_sprite.draw()

                # prepare player object
                player = prepare_player_object(img)
                
                # prepare field. The field is a white rectangle in the middle of the image to deny the player to move through it
                # and keep the ball on the other half
                prepare_field(player)

                # Draw vertical line over center of screen to divide the screen in half and display the game field
                #pg.graphics.draw(2, pg.gl.GL_LINES, ('v2i', (WINDOW_WIDTH//2, 0, WINDOW_WIDTH//2, WINDOW_HEIGHT)))

                # Draw two more vertical lines to show the player where the "field" is
                #pg.graphics.draw(2, pg.gl.GL_LINES, ('v2i', (WINDOW_WIDTH//3, 0, WINDOW_WIDTH//3, WINDOW_HEIGHT)))
                #pg.graphics.draw(2, pg.gl.GL_LINES, ('v2i', (WINDOW_WIDTH*2//3, 0, WINDOW_WIDTH*2//3, WINDOW_HEIGHT)))

                if ball.check_collision(player):
                    ball.change_direction()
                ball.move()
                
                # show score as label
            
            pg.text.Label(text=str(ball.score), x=WINDOW_WIDTH//2, y=WINDOW_HEIGHT-20, anchor_x='center').draw()    
            ball.draw()

            
        

pg.app.run()