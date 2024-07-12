
import sys
print('sklearn' in sys.modules)

import pymurapi as mur
from time import sleep
import cv2 as cv
from sklearn.neighbors import KNeighborsClassifier

# Initialize MurAPI and retrieve image dimensions
auv = mur.mur_init()
auv.get
height, width = auv.get_image_bottom().shape[:2]

# Test func
def col(image, contours):
    cv.drawContours(image, contours, -1, (0, 255, 0), 3)
    cv.imshow('', image)
    cv.waitKey(1)


def go_to_box():
    dict_depth: dict[str, float] = {"1": 3.7, "2": 3.25, "3": 2.85}
    image = auv.get_image_bottom()

    knn = KNeighborsClassifier(n_neighbors=1)

    # Для начала загружаем и подготавливаем изображение
    # image 
    _, binary_image = cv.threshold(image, 127, 255, cv.THRESH_BINARY_INV)

    # Определяем контуры и последовательно предсказываем распознаваемые цифры
    contours, _ = cv.findContours(binary_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv.boundingRect(contour)
        roi = binary_image[y:y+h, x:x+w]
        digit = knn.predict(roi.flatten().reshape(1, -1))[0]

def move_to_direction() -> None:
    """
    Adjusts AUV orientation to a specified direction.
    """
    yaw_ = auv.get_yaw()
    auv.set_motor_power(0, 25)
    auv.set_motor_power(1, -25)
    sleep(1)
    yaw = auv.get_yaw()
    while abs(yaw_ - auv.get_yaw()) > 12:
        print(abs(yaw_ - auv.get_yaw())) # if delete this line than code doesn`t work
        
    else:
        auv.set_motor_power(0, 0)
        auv.set_motor_power(1, 0)


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


def search_object(image, error_size = 35) -> tuple[str, str, float, float]:
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
            if abs(width / 2 - x) < error_size and abs(height / 2 - y) < error_size:
                try:
                    color = search_color(image, x, y)
                    col(image, contours)

                    return name_figure[len(approx)], color, x, y

                except KeyError:
                    pass  # Handle unknown figure types


def git_object_color() -> tuple[str, str, float, float]:
    hashes = []
    while len(hashes) <= 5:
        image = auv.get_image_bottom()
        returned = search_object(image)

        if returned: hashes.append(returned)

    list_objects = [hash_[0] for hash_ in hashes]
    list_colors = [hash_[1] for hash_ in hashes]

    x_coords = [hash_[-2] for hash_ in hashes]
    y_coords = [hash_[-1] for hash_ in hashes]

    most_common_object = max(set(list_objects), key=lambda x: (list_objects.count(x), -list_objects.index(x)))
    most_common_color = max(set(list_colors), key=lambda x: (list_colors.count(x), -list_colors.index(x)))

    x_mean = sum(x_coords) / len(x_coords)
    y_mean = sum(y_coords) / len(y_coords)

    return most_common_object, most_common_color, x_mean, y_mean


while True:
    print(git_object_color())
    go_to_box()
