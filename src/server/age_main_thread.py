import threading
import time
import cv2
import copy
import numpy as np
import pyautogui
import configparser
import sys

from src.server.age_unit_server import UnitServer
from src.server.age_grabber_thread import GrabberThread
from src.server.face_detection_thread import FaceDetectionThread
from src.server.age_recognition_thread import RecognitionThread
from utils.folder_file_manager import log_print
from settings import CONFIRM_FRAME_RATE


class AgeGuessingMainThread(threading.Thread):

    def __init__(self, parameters, parent):

        threading.Thread.__init__(self)
        self.parent = parent
        self.terminated = False
        self.caption = parameters.get("window", "caption_AG")
        self.annotation_list = []
        self.age = 0
        self.message = ""
        self.db_saved_statue = ""
        self.db_saved_date = ""
        self.age_guessed_time = 0
        self.stop_flag = False
        self.min_detections = int(parameters.get("recognition", "min_detections"))

        self.display_size = parameters.get("window", "display_size")
        self.display_size = self.display_size.upper().split("X")
        self.display_size = tuple([int(s) for s in self.display_size])

        # Get current resolution
        self.resolution = pyautogui.size()
        self.resolution = [int(s) for s in self.resolution]
        print(self.resolution)

        queue_length = 8
        self.unit_server = UnitServer(queue_length)

        # Start Grabber thread
        self.grabber_thread = GrabberThread(self, parameters)
        self.grabber_thread.start()

        # Start Detection thread
        self.faces = []
        self.detection_thread = FaceDetectionThread(self, parameters)
        self.detection_thread.start()

        # Start Recognition Thread
        self.recognition_thread = RecognitionThread(self, parameters)
        self.recognition_thread.start()

        # self.find_face_encoding_thread = Thread(target=self.find_face_encoding)
        # self.find_face_encoding_thread.start()

        unused_width = self.resolution[0] - self.display_size[0]
        cv2.moveWindow(self.caption, unused_width // 2, 0)
        # Will move window when everything is running. Better way TODO

    def run(self):

        while not self.terminated:
            time.sleep(0.5)

    def put_unit(self, unit):

        # Show the newest frame immediately.
        self.show_video(unit)

        # Send to further processing
        if not self.terminated:
            self.unit_server.put_unit(unit)

    def get_unit(self, caller, timestamp=None):

        return self.unit_server.get_unit(caller, timestamp)

    def terminate(self):

        self.terminated = True

    def draw_bounding_box(self, img, bbox):

        x, y, w, h = [int(c) for c in bbox]
        face_img = img[y:y + h, x:x + w]

        # ------------ send cropped face image  -------
        self.parent.person_face_image_list.append(face_img)

        # ------------------------------------------------------
        m = 0.2

        # Upper left corner
        pt1 = (x, y)
        pt2 = (int(x + m * w), y)
        cv2.line(img, pt1, pt2, color=[255, 255, 0], thickness=2)

        pt1 = (x, y)
        pt2 = (x, int(y + m * h))
        cv2.line(img, pt1, pt2, color=[255, 255, 0], thickness=2)

        # Upper right corner
        pt1 = (x + w, y)
        pt2 = (x + w, int(y + m * h))
        cv2.line(img, pt1, pt2, color=[255, 255, 0], thickness=2)

        pt1 = (x + w, y)
        pt2 = (int(x + w - m * w), y)
        cv2.line(img, pt1, pt2, color=[255, 255, 0], thickness=2)

        # Lower left corner
        pt1 = (x, y + h)
        pt2 = (x, int(y + h - m * h))
        cv2.line(img, pt1, pt2, color=[255, 255, 0], thickness=2)

        pt1 = (x, y + h)
        pt2 = (int(x + m * w), y + h)
        cv2.line(img, pt1, pt2, color=[255, 255, 0], thickness=2)

        # Lower right corner
        pt1 = (x + w, y + h)
        pt2 = (x + w, int(y + h - m * h))
        cv2.line(img, pt1, pt2, color=[255, 255, 0], thickness=2)

        pt1 = (x + w, y + h)
        pt2 = (int(x + w - m * w), y + h)
        cv2.line(img, pt1, pt2, color=[255, 255, 0], thickness=2)

    def refresh(self):
        self.faces = []
        self.annotation_list = []

    def draw_face(self, face, img):

        bbox = np.mean(face['bboxes'], axis=0)

        self.draw_bounding_box(img, bbox)
        x, y, w, h = [int(c) for c in bbox]

        if self.annotation_list.__len__() == CONFIRM_FRAME_RATE:
            if "Rot" in self.annotation_list:
                if "Gelb" in self.annotation_list:
                    self.message = "[Ausweis zeigen!]"
                    # self.parent.send_active_signal_flag = True
                    self.parent.send_yellow_signal_flag = True
                else:
                    self.message = "[Nicht erlaubt!]"
                    self.parent.send_red_signal_flag = True
            if "Gruen" in self.annotation_list:

                # self.message = "[Erlaubt!]"
                # self.parent.send_green_signal_flag = True
                # self.parent.calced_age = self.age

                if "Gelb" in self.annotation_list:
                    self.message = "[Ausweis zeigen!]"
                    # self.parent.send_active_signal_flag = True
                    self.parent.send_yellow_signal_flag = True
                else:
                    self.message = "[Erlaubt!]"
                    self.parent.send_green_signal_flag = True
                    self.parent.calc_age = self.age

            if "Gelb" in self.annotation_list:
                self.message = "[Ausweis zeigen!]"
                # self.parent.send_active_signal_flag = True
                self.parent.send_yellow_signal_flag = True

            self.age_guessed_time = time.time()
            self.stop_flag = True
            self.refresh()
        else:
            if "age" in list(face.keys()):

                age_label = ""

                age = face['age'] - 2
                if age < 19:
                    age_label = "Rot"
                if 18 < age < 24:
                    age_label = "Gelb"
                if age > 24:
                    age_label = "Gruen"
                self.age = int(age)
                annotation = age_label + '' + " : %.0f" % age
                self.annotation_list.append(age_label)
                txt_loc = (x, y + h + 30)
                cv2.putText(img,
                            text=annotation,
                            org=txt_loc,
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=1,
                            color=[255, 255, 0],
                            thickness=2)

    def draw_result_message(self, frame):
        if self.message == "[Ausweis zeigen!]":
            cv2.putText(frame, self.message, (50, 100), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 255, 0), 2)
            # self.parent.send_active_signal_flag = True

        if self.message == "[Erlaubt!]":
            cv2.putText(frame, self.message, (150, 250), cv2.FONT_HERSHEY_TRIPLEX, 2, (0, 0, 255), 4)
            if self.db_saved_date != "":
                cv2.putText(frame, "Checked date:" + self.db_saved_date, (150, 300), cv2.FONT_HERSHEY_TRIPLEX, 1,
                            (0, 255, 0), 2)
                cv2.putText(frame, "Checked statue:" + self.db_saved_statue, (150, 350), cv2.FONT_HERSHEY_TRIPLEX, 1,
                            (0, 255, 0), 2)

            now_time = time.time()
            if now_time - self.age_guessed_time >= 5:
                self.stop_flag = False
                self.recognition_thread.check_db_flag = False
                self.db_saved_date = ""
                self.db_saved_statue = ""

        if self.message == "[Nicht erlaubt!]":
            cv2.putText(frame, self.message, (50, 250), cv2.FONT_HERSHEY_TRIPLEX, 2, (0, 0, 255), 4)
            if self.db_saved_date != "":
                cv2.putText(frame, "Checked date:" + self.db_saved_date, (50, 300), cv2.FONT_HERSHEY_TRIPLEX, 1,
                            (0, 255, 0), 2)
                cv2.putText(frame, "Checked statue:" + self.db_saved_statue, (50, 350), cv2.FONT_HERSHEY_TRIPLEX, 1,
                            (0, 255, 0), 2)

            now_time = time.time()
            if now_time - self.age_guessed_time >= 5:
                self.stop_flag = False
                self.recognition_thread.check_db_flag = False
                self.db_saved_date = ""
                self.db_saved_statue = ""

        if self.message == "[Check Yourself!]":
            cv2.putText(frame, self.message, (10, 250), cv2.FONT_HERSHEY_TRIPLEX, 2, (0, 0, 255), 4)
            now_time = time.time()
            if now_time - self.age_guessed_time >= 5:
                self.recognition_thread.check_db_flag = False
                self.stop_flag = False

    def show_video(self, unit):

        unit.acquire()
        frame = copy.deepcopy(unit.get_frame())
        unit.release()

        if not self.stop_flag:
            valid_faces = [f for f in self.faces if len(f['bboxes']) >= self.min_detections]

            for face in valid_faces:
                self.draw_face(face, frame)

        if self.stop_flag:
            self.draw_result_message(frame)
            self.refresh()

        # -------- show frame -----------
        cv2.imshow("Age system", frame)

        # -----------------------------------------

        key = cv2.waitKey(10)
        if key == 27:
            self.terminate()

    def find_nearest_face(self, bbox):

        distances = []

        x, y, w, h = bbox
        bbox_center = [x + w / 2, y + h / 2]

        for face in self.faces:
            x, y, w, h = np.mean(face['bboxes'], axis=0)
            face_center = [x + w / 2, y + h / 2]

            distance = np.hypot(face_center[0] - bbox_center[0],
                                face_center[1] - bbox_center[1])

            distances.append(distance)

        if len(distances) == 0:
            min_idx = None
            min_distance = None
        else:
            min_distance = np.min(distances)
            min_idx = np.argmin(distances)

        return min_idx, min_distance

    def set_detections(self, detections, timestamps):

        # Find the location among all recent face locations where this would belong

        for bbox, timestamp in zip(detections, timestamps):

            idx, dist = self.find_nearest_face(bbox)
            try:
                if dist is not None and dist < 100:

                    self.faces[int(idx)]['bboxes'].append(bbox)
                    self.faces[int(idx)]['timestamps'].append(timestamp)

                    if len(self.faces[int(idx)]['bboxes']) > 7:
                        self.faces[int(idx)]['bboxes'].pop(0)
                        self.faces[int(idx)]['timestamps'].pop(0)

                else:
                    # This is a new face not in the scene before
                    self.faces.append({'timestamps': [timestamp], 'bboxes': [bbox]})
            except Exception as e:
                log_print(info_str=e)

        # Clean old detections:

        now = time.time()
        faces_to_remove = []

        for i, face in enumerate(self.faces):
            if now - face['timestamps'][-1] > 0.5:
                faces_to_remove.append(i)

        for i in faces_to_remove:
            try:
                self.faces.pop(i)
            except Exception as e:
                # Face was deleted by other thread.
                log_print(info_str=e)

    def get_faces(self):

        if len(self.faces) == 0:
            return None
        else:
            return self.faces

    def is_terminated(self):

        return self.terminated


if __name__ == '__main__':

    help_message = '''
    USAGE: Main.py [params file]
    '''

    if len(sys.argv) > 1:
        paramFile = sys.argv[1]
    else:
        paramFile = "config.ini"

    params = configparser.ConfigParser()
    params.read(paramFile)

    # Initialize controller thread

    AgeGuessingMainThread = AgeGuessingMainThread(parameters=params, parent=None)
    AgeGuessingMainThread.start()
