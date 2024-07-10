import cv2 as cv
import pymurapi as mur
from time import sleep

auv = mur.mur_init()
blue:  tuple = (255, 0, 0)
green: tuple = (0, 255, 0)
red:   tuple = (0, 0, 255)

# Test func
def drawContur(img, conrour) -> None:
    cv.drawContours(img, [conrour], 0, red, 5)
    cv.imshow('', img)
    cv.waitKey(1)

def search_coordinates(contours) -> tuple[int, int]:
    if contours is None: return None
    try:
        moments = cv.moments(contours[0])
        x = moments['m10'] / moments['m00']
        y = moments["m01"] / moments["m00"]
        return x, y
    except ZeroDivisionError:
        return None
    except  IndexError:
        return None
    
def search_object(image) -> str:
    name_figure: dict[int, str] = {3: 'Triangle', 4: 'Quadrilateral'}
    hsv_low, hsv_max = (25, 100, 100), (150, 255, 255)

    image_hsv  = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    img = cv.inRange(image_hsv, hsv_low, hsv_max)
    blurred = cv.GaussianBlur(img, (5, 5), 0)

    mask = cv.Canny(blurred, 50, 150, apertureSize=3)

    contours, _ =cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    for conrour in contours:
        approx = cv.approxPolyDP(conrour, 0.05 * cv.arcLength(conrour, True), True)

        try:
            print(name_figure[len(approx)])# is test func
            drawContur(image, conrour)     # is test func
            search_coordinates(contours)

            return name_figure[len(approx)]
        except KeyError:
            continue

def ride_red_line(image):
    img = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    hsv_low, hsv_max = (0, 3, 20), (27, 255, 255)

    mask = cv.inRange(image, hsv_low, hsv_max)

    contours, _ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    coordinates = search_coordinates(contours)
    if coordinates is not None:
        x, y = coordinates
        cv.circle(image, (int(x), int(y)), 5, (0, 255, 0))
        cv.imshow('', image)
        cv.waitKey(1)



# Test func
while True:
    sleep(0)
    image = auv.get_image_bottom()
    ride_red_line(image)