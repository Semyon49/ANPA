import cv2 as cv
import pymurapi as mur


auv = mur.mur_init()

image = auv.get_image_bottom()
height, width = image.shape[:2]

def search_circle(image, ) -> bool:
    ...

def search_triangle(image, ) -> bool:
    ...

def search_square(image, ) -> bool:
    ...