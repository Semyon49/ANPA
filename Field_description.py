import cv2 as cv
import pymurapi as mur
from time import sleep

auv = mur.mur_init()
blue:  tuple = (255, 0, 0)
green: tuple = (0, 255, 0)
red:   tuple = (0, 0, 255)


def drawContur(img, conrour):
    cv.drawContours(img, [conrour], 0, red, 5)
    cv.imshow('', img)
    cv.waitKey(1)

def search_object(image) -> str:
    hash_figure: list = []
    name_figure: dict[int, str] = {0: 'Circle', 3: 'Triangle', 4: 'Quadrilateral'}

    img  = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    hsv_low, hsv_max = (25, 100, 100), (150, 255, 255)

    mask = cv.inRange(img, hsv_low, hsv_max)
    contours, _ =cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    for conrour in contours:
        approx = cv.approxPolyDP(conrour, 0.01 * cv.arcLength(conrour, True), True)
        
        try:
            if name_figure[len(approx)] is None: continue
            if len(approx) < 5: print(name_figure[len(approx)])
            drawContur(img, conrour)
        except  KeyError:
            sleep(0.1)
    
# Test
while True:
    sleep(0)
    image = auv.get_image_bottom()
    search_object(image)