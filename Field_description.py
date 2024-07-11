import cv2 as cv
import pymurapi as mur
from time import sleep

# Initialize MurAPI and retrieve image dimensions
auv = mur.mur_init()
image = auv.get_image_bottom()
height, width = image.shape[:2]

# Define colors as tuples
blue = (255, 0, 0)
green = (0, 255, 0)
red = (0, 0, 255)


# def move_to_direction(power=25):
#     """
#     Adjusts AUV orientation to a specified direction.
#     """
#     yaw_ = auv.get_yaw()
#     auv.set_motor_power(0, power)
#     auv.set_motor_power(1, -power)
#     sleep(0.5)
#     while abs(yaw_ - auv.get_yaw()) > 10:
#         power = abs(yaw_ - auv.get_yaw()) * 0.3
#         auv.set_motor_power(0, power)
#         auv.set_motor_power(1, -power)

#     auv.set_motor_power(0, 0)
#     auv.set_motor_power(1, 0)


def search_coordinates(contour) -> tuple[float, float]:
    """
    Finds centroid coordinates of a contour.
    """
    try:
        moments = cv.moments(contour)
        x = moments['m10'] / moments['m00']
        y = moments['m01'] / moments['m00']
        return x, y
    except ZeroDivisionError:
        return None
    except IndexError:
        return None


def search_color(image, x, y) -> str:
    """
    Determines color at specified coordinates in an image.
    """
    color = image[int(y), int(x)]
    yellow_min, yellow_max = (0, 142, 155), (70, 216, 255)
    black_min, black_max = (0, 0, 0), (20, 256, 20)

    if all(yellow_min[i] <= color[i] <= yellow_max[i] for i in range(3)):
        return 'yellow'
    if all(black_min[i] <= color[i] <= black_max[i] for i in range(3)):
        return 'black' 


def search_object(image) -> tuple[str, str, float, float]:
    """
    Detects and identifies geometric objects in an image.
    """
    name_figure = {3: 'Triangle', 4: 'Quadrilateral'}
    hsv_low, hsv_max = (25, 100, 0), (150, 255, 255)

    image_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    img = cv.inRange(image_hsv, hsv_low, hsv_max)
    blurred = cv.GaussianBlur(img, (5, 5), 0)
    mask = cv.Canny(blurred, 50, 150, apertureSize=3)

    contours, _ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)

    for contour in contours:
        approx = cv.approxPolyDP(contour, 0.05 * cv.arcLength(contour, True), True)

        if search_coordinates(contour) is not None:
            x, y = search_coordinates(contour)
            if abs(width / 2 - x) < 35 and abs(height / 2 - y) < 35:
                try:
                    color = search_color(image, x, y)
                    cv.drawContours(image, contours, -1, (0, 255, 0), 3)
                    cv.imshow('', image)
                    cv.waitKey(1)

                    return name_figure[len(approx)], color, x, y

                except KeyError:
                    pass  # Handle unknown figure types

def git_object_color() -> tuple[str, str, float, float]:
    hash = []
    while len(hash) <= 5:
        image = auv.get_image_bottom()
        returned = search_object(image)

        if returned: hash.append(returned)

    list_object = [hash[i][0] for i in range(len(hash))]
    list_color  = [hash[i][1] for i in range(len(hash))]

    x = [hash[i][-2] for i in range(len(hash))]
    y = [hash[i][-1] for i in range(len(hash))]

    most_common_object = max(set(list_object), key=lambda x: (list_object.count(x), -list_object.index(x)))
    most_common_color = max(set(list_color), key=lambda x: (list_color.count(x), -list_color.index(x)))

    x_ = sum(x)/len(x)
    y_ = sum(y)/len(y)

    return most_common_object, most_common_color, x_, y_



move_to_direction()

# while True:
#     sleep(0)
#     print(git_object_color())