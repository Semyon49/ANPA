import cv2 as cv
import pymurapi as mur
from time import sleep

auv = mur.mur_init()
image = auv.get_image_bottom()
height, width = image.shape[:2]
speed = 10
blue:  tuple = (255, 0, 0)
green: tuple = (0, 255, 0)
red:   tuple = (0, 0, 255)


def search_coordinates(contours) -> tuple[int, int]:
    try:
        moments = cv.moments(contours[0])
        x = moments['m10'] / moments['m00']
        y = moments["m01"] / moments["m00"]
        return x, y
    except ZeroDivisionError:
        return None
    except IndexError:
        return None
    
def search_color(image, x, y):
    color = image[int(y), int(x)]
    yellow_min, yellow_max = (0, 142, 155), (70, 216, 255)
    black_min, black_max = (0, 0, 0), (20, 256, 20)
    print(color)
    if all(yellow_min[i] <= color[i] <= yellow_max[i] for i in range(3)):
        print('yellow')
    if all(black_min[i] <= color[i] <= black_max[i] for i in range(3)):
        print('black')

def search_object(image) -> tuple[str, int, int]:
    name_figure: dict[int, str] = {3: 'Triangle', 4: 'Quadrilateral'}
    hsv_low, hsv_max = (25, 100, 0), (150, 255, 255)

    image_hsv  = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    img = cv.inRange(image_hsv, hsv_low, hsv_max)
    blurred = cv.GaussianBlur(img, (5, 5), 0)

    mask = cv.Canny(blurred, 50, 150, apertureSize=3)

    contours, _ =cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)

    for conrour in contours:
        approx = cv.approxPolyDP(conrour, 0.05 * cv.arcLength(conrour, True), True)

        if search_coordinates(contours) is not None: 
            x, y = search_coordinates(contours)
            if abs(width / 2 - x) < 25 and abs(height / 2 - y) < 35:
                try:
                    print(name_figure[len(approx)])# is test func
                    search_color(image, x, y)
                    cv.drawContours(image, contours, -1, (0,255,0), 3)
                    cv.imshow('',image)
                    cv.waitKey(1)

                    return name_figure[len(approx)], x, y
                
                except KeyError:
                    ...

# Test func
while True:
    sleep(0)
    image = auv.get_image_bottom()
    search_object(image)