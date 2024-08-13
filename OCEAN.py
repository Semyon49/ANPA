import time
import cv2 as cv
import numpy as np
import pymurapi as mur

        
class Config:
    def __init__(self):
        self.settings = {
            # Picture settings
            # do not for customization
            'hsv_value': 10,
            'hsv_max': 120,
            'hsv_min': 0,
            'hsv_dispersion': 25,
            'SValue_min': 50,
            'VValue_min': 50,
            'SValue_max': 255,
            'VValue_max': 255,
            'iR_iterations': ...,
            'white_min': 1.7,
            'white_max': 16.0,
            
            # Driving settings
            'turn_angle': 7,
            'shift_max': 20,
            'shift_step': 0.3,
            'turn_step': 10,
            'straight_run': 0.2,
            'find_turn_attempts': 5,
            'find_turn_step': 0.3,
            'max_steps': 100
        }
        self.settings['iR_iterations'] = int((self.settings['hsv_max'] - self.settings['hsv_min']) / self.settings['hsv_dispersion'])


class GOEM():
    def calc_line(self, x1, y1, x2, y2):
        a = float(y2 - y1) / (x2 - x1) if x2 != x1 else 0
        b = y1 - a * x1
        return a, b

    def order_box(self, box):
        srt = np.argsort(box[:, 1])
        btm1 = box[srt[0]]
        btm2 = box[srt[1]]

        top1 = box[srt[2]]
        top2 = box[srt[3]]

        bc = btm1[0] < btm2[0]
        btm_l = btm1 if bc else btm2
        btm_r = btm2 if bc else btm1

        tc = top1[0] < top2[0]
        top_l = top1 if tc else top2
        top_r = top2 if tc else top1

        return np.array([top_l, top_r, btm_r, btm_l])
    
    def get_horz_shift(self, x, w):
        hw = w / 2
        return 100 * (x - hw) / hw

    def get_vert_angle(self, p1, p2, w, h):
        px1 = p1[0] - w/2
        px2 = p2[0] - w/2
        
        py1 = h - p1[1]
        py2 = h - p2[1]

        angle = 90
        if px1 != px2:
            a, b = self.calc_line(px1, py1, px2, py2)
            angle = 0
            if a != 0:
                x0 = -b/a
                y1 = 1.0
                x1 = (y1 - b) / a
                dx = x1 - x0
                tg = y1 * y1 / dx / dx
                angle = 180 * np.arctan(tg) / np.pi
                if a < 0:
                    angle = 180 - angle
        return angle

    def calc_line_length(self, p1, p2):
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return (dx * dx + dy * dy) ** 0.5
    
    def calc_box_vector(self, box):
        v_side = self.calc_line_length(box[0], box[3])
        h_side = self.calc_line_length(box[0], box[1])
        idx = [0, 1, 2, 3]
        if v_side < h_side:
            idx = [0, 3, 1, 2]
        return ((box[idx[0]][0] + box[idx[1]][0]) / 2, (box[idx[0]][1] + box[idx[1]][1]) / 2), ((box[idx[2]][0] + box[idx[3]][0]) / 2, (box[idx[2]][1]  +box[idx[3]][1]) / 2)


class ROI:
    area = 0
    vertices = None

    def init_roi(self, width, height):
        vertices = [(0, height), (width / 4, 3 * height / 4),(3 * width / 4, 3 * height / 4), (width, height),]
        self.vertices = np.array([vertices], np.int32)
        
        blank = np.zeros((height, width, 3), np.uint8)
        blank[:] = (255, 255, 255)
        blank_gray = cv.cvtColor(blank, cv.COLOR_BGR2GRAY)
        blank_cropped = self.crop_roi(blank_gray)
        self.area = cv.countNonZero(blank_cropped)

    def crop_roi(self, img):
        mask = np.zeros_like(img)
        match_mask_color = 255
        
        cv.fillPoly(mask, self.vertices, match_mask_color)
        
        masked_image = cv.bitwise_and(img, mask)
        
        return masked_image

    def get_area(self):
        return self.area

    def get_vertices(self):
        return self.vertices


class OCEAN(GOEM):
    # OCEAN — Optimized Control Engine for Auto Navigation

    def __init__(self):
        self.config = Config().settings
        self.Roi = ROI()

        self.auv = mur.mur_init()


    def balance_pic(self, image):
        self.HV =  self.config['hsv_value']
        ret = None
        direction = 0

        for i in range(0, self.config['iR_iterations']):

            gray = cv.cvtColor(image, cv.COLOR_BGR2HSV)
            mask = cv.inRange(gray,(self.HV - 0.5 * self.config['hsv_dispersion'], self.config['SValue_min'], self.config['VValue_min']),
                                        (self.HV + 0.5 * self.config['hsv_dispersion'], self.config['SValue_max'], self.config['VValue_max']))

            crop = self.Roi.crop_roi(mask)
            nwh = cv.countNonZero(crop)

            perc = 100 * nwh / self.Roi.get_area()
        

            # print("iterations = {}, hsv_value = {}, perc = {}".format(i, self.HV, perc))

            if perc > self.config['white_max']:
                if self.HV > self.config['hsv_max'] - 0.5 * self.config['hsv_dispersion']:
                    break
                if direction == -1:
                    ret = mask
                    break
                self.HV -= self.config['hsv_dispersion']
                direction = 1

            elif perc < self.config['white_min']:
                if self.HV < self.config['hsv_min'] - 0.5 * self.config['hsv_dispersion']:
                    break
                if  direction == 1:
                    ret = mask
                    break

                self.HV += self.config['hsv_dispersion']
                direction = -1
            else:
                ret = mask
                break 

        return ret      

    def prepare_pic(self, image):
        height, width = image.shape[:2]

        if self.Roi.get_area() == 0:
            self.Roi.init_roi(width, height)

        return self.balance_pic(image), width, height

    def find_main_countour(self, image):
        cnts, _ = cv.findContours(image, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)

        C = None
        if cnts is not None and len(cnts) > 0:
            C = max(cnts, key = cv.contourArea)

        if C is None:
            return None, None

        rect = cv.minAreaRect(C)
        box = cv.boxPoints(rect)
        box = np.intp(box)

        box = geom.order_box(box)

        return C, box

    def handle_pic(self, fout = None, show = True):
        # image = cv.imread('107.png')
        image = self.auv.get_image_bottom()

        if image is None:
            raise Exception(("Video not found"))
            ...

        cropped, w, h = self.prepare_pic(image)
        if cropped is None:
            return None, None
        cont, box = self.find_main_countour(cropped)
        if cont is None:
            return None, None

        p1, p2 = self.calc_box_vector(box)
        p1 = list(map(int, p1))
        p2 = list(map(int, p2))

        if p1 is None: return None, None

        angle = self.get_vert_angle(p1, p2, w, h)
        shift = self.get_horz_shift(p1[0], w)

        draw = fout is not None or show

        if draw:
            cv.drawContours(image, [cont], -1, (0,0,255), 3)
            cv.drawContours(image,[box],0,(255,0,0),2)
            cv.line(image, p1, p2, (0, 255, 0), 3)
            msg_a = "Angle {0}".format(int(angle))
            msg_s = "Shift {0}".format(int(shift))

            cv.putText(image, msg_a, (10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            cv.putText(image, msg_s, (10, 40), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        if fout is not None:
            cv.imwrite(fout, image)

        if show:    
            cv.imshow("Image", image)
            cv.waitKey(1)

        return angle, shift

    def display_config(self):
        for key, value in self.config.items():
            print('{} = {}'.format(key, value))

    def set_motors(self, mode):
        if mode == 'L':
            self.auv.set_motor_power(0, 25)
            self.auv.set_motor_power(1, 0)
        elif mode == 'R':
            self.auv.set_motor_power(0, 0)
            self.auv.set_motor_power(1, 25)



    def turn(self, r, t):
        turn_cmd = 'R' if r < 0 else 'L'
        ret_cmd = 'L' if r < 0 else 'R'
        turn = "Right" if r < 0 else "Left"

        print("Turn", turn, t)

        self.set_motors(turn_cmd)
        time.sleep(t)
        self.auv.set_motor_power(0, 0)
        self.auv.set_motor_power(1, 0)


    def get_vector(self):
        angle, shift = self.handle_pic()
        return angle, shift
    
    def find_line(self, side):

        if side == 0:
            return None, None
            
        for _ in range(0, self.config['find_turn_attempts']):
            self.turn(side, self.config['find_turn_step'])
            angle, shift = self.get_vector()
            if angle is not None:
                return angle, shift

        return None, None

    def get_turn(self, turn_state, shift_state):
        turn_dir = 0
        turn_val = 0
        if shift_state != 0:
            turn_dir = shift_state
            turn_val = self.config['shift_step'] if shift_state != turn_state else self.config['turn_step']
        elif turn_state != 0:
            turn_dir = turn_state
            turn_val = self.config['turn_step']
        return turn_dir, turn_val   

    def check_shift_turn(self, angle, shift):
        turn_state = 0
        if angle < self.config['turn_angle'] or angle > 180 - self.config['turn_angle']:
            turn_state = np.sign(90 - angle)

        shift_state = 0
        if abs(shift) > self.config['shift_max']:
            shift_state = np.sign(shift)
        return turn_state, shift_state
    

    def follow(self, iterations):
        self.auv.set_motor_power(0, 25)
        self.auv.set_motor_power(1, 25)

        # try:
        try:
            last_turn = 0
            last_angle = 0 

            for i in range(0, iterations):
                a, shift = self.get_vector()
                if a is None:
                    if last_turn != 0:
                        a, shift = self.find_line(last_turn)
                        if a is None:
                            break
                    elif last_angle != 0:
                        print("Looking for line by angle", last_angle)
                        self.turn(np.sign(90 - last_angle), self.config['turn_step'])
                        continue
                    else:
                        break

                print((i, "Angle", a, "Shift", shift))

                turn_state, shift_state = self.check_shift_turn(a, shift)

                turn_dir, turn_val = self.get_turn(turn_state, shift_state)

                if turn_dir != 0:
                    self.turn(turn_dir, turn_val)
                    last_turn = turn_dir
                else:
                    time.sleep(self.config['straight_run']/2)
                    last_turn = 0
                last_angle = a
            
        finally:
            self.auv.set_motor_power(0, 25)
            self.auv.set_motor_power(1, 25)
            time.sleep(0.05)



if __name__ == "__main__":
    geom = GOEM()
    LLM = OCEAN()
    LLM.display_config()
    while True:
        LLM.follow(500)



