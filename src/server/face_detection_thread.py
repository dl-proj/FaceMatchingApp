import threading
import time

from utils.face_detector import detect_face_haar


class FaceDetectionThread(threading.Thread):

    def __init__(self, parent, parameters):
        self.terminated = False
        threading.Thread.__init__(self)

        print("Initializing detection thread...")
        self.parent = parent

        # Image input size, must match the network
        self.width = int(parameters.get("detection", "input_width"))
        self.height = int(parameters.get("detection", "input_height"))

    def terminate(self):
        self.terminated = True

    def run(self):

        while not self.parent.is_terminated() and not self.terminated:

            unit = None

            while unit is None:

                unit = self.parent.get_unit(self)
                if unit is None:  # No units available yet
                    time.sleep(0.1)

                if self.parent.is_terminated():
                    break

            if self.parent.is_terminated():
                break

            img = unit.get_frame()

            detection_img = img.copy()
            unit.release()

            faces = detect_face_haar(frame=detection_img)
            b_boxes = []
            timestamps = []

            for detection in faces:
                left, top, right, bottom = detection
                width = right - left
                height = bottom - top
                b_boxes.append([left, top, width, height])
                timestamps.append(unit.get_time_stamp())

            self.parent.set_detections(b_boxes, timestamps)
