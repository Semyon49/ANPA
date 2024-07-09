import cv2 as cv
import pymurapi as mur
import time

auv = mur.mur_init()
hash_figure: list = []
red: tuple = (0, 0, 255)

def search_object(image) -> str:
    name_figure: dict[int, str] = {0: 'Circle', 3: 'Triangle', 4: 'Quadrilateral'}

    img  = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    hsv_low: tuple = (5, 100, 100)
    hsv_max: tuple = (150, 255, 255)

    mask = cv.inRange(img, hsv_low, hsv_max)

    contours, _ =cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    for conrour in contours:
        approx = cv.approxPolyDP(conrour, 0.01 * cv.arcLength(conrour, True), True)

        if len(approx) in (1, 2): continue
        cv.drawContours(image, [conrour], 0, red, 5)
        cv.imshow('', image)
        cv.waitKey(1)

        if len(approx) < 5: return name_figure[len(approx)]
    
# Test
while True:
    time.sleep(0)
    image = auv.get_image_bottom()
    print(search_object(image))