# -*- coding: utf-8 -*-

import threading
import cv2
from utils import grab_unit


class GrabberThread(threading.Thread):

    def __init__(self, parent, params):

        threading.Thread.__init__(self)

        cam_id = params.getint("camera", "age_guess_id")
        cam_resolution = params.get("camera", "resolution")
        cam_resolution = cam_resolution.upper().split("X")
        cam_resolution = [int(x) for x in cam_resolution]
        print(("Using camera %d at resolution %s" % (cam_id, cam_resolution)))

        self.flipHor = params.getint("camera", "flip_horizontal")

        self.video = cv2.VideoCapture(0)  # 0: Laptop camera, 1: USB-camera
        # self.video.set(3 , 640  ) # width
        # self.video.set(4 , 480  ) # height
        # self.video.set(10, 10  ) # brightness     min: 0   , max: 255 , increment:1
        # self.video.set(11, 10   ) # contrast       min: 0   , max: 255 , increment:1
        # self.video.set(12, 70   ) # saturation     min: 0   , max: 255 , increment:1
        # self.video.set(13, 13   ) # hue
        # self.video.set(14, 10   ) # gain           min: 0   , max: 127 , increment:1
        # self.video.set(15, -3   ) # exposure       min: -7  , max: -1  , increment:1
        # self.video.set(17, 5000 ) # white_balance  min: 4000, max: 7000, increment:1
        # self.video.set(28, 0    ) # focus          min: 0   , max: 255 , increment:5
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        print(self.fps)
        self.parent = parent

        print("Initializing grabber thread...")

    def run(self):

        while not self.parent.is_terminated():

            stat, frame = self.video.read()
            frame = cv2.flip(frame, 1)

            if frame is not None and not self.parent.is_terminated():
                if self.flipHor:
                    # frame = frame[:, ::-1, ...]
                    frame = cv2.flip(frame, 0)

                unit = grab_unit.GrabUnit(frame)

                self.parent.put_unit(unit)
