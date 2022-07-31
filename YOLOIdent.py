from yolo import YOLO
from PIL import Image
import numpy as np
import cv2


class UseYOLO():
    def __init__(self):
        self.yolo = YOLO()

    def start(self, frame):
        # 格式转变，BGRtoRGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 转变成Image
        frame = Image.fromarray(np.uint8(frame))
        # 进行检测
        frame = np.array(self.yolo.detect_image(frame))
        # print(frame)
        return frame
