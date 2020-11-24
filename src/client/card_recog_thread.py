import cv2
import threading
import time
import datetime

from src.client.birth_ocr import extract_birthday
from imutils.video.pivideostream import PiVideoStream
from utils.folder_file_manager import log_print
from utils.face_detector import detect_face_haar
from settings import ID_TYPE, FACE_MARGIN


class CardRecognitionThread(threading.Thread):

    def __init__(self, win):
        threading.Thread.__init__(self)
        self.window = win
        self.resolution = (800, 600)

        self.vs = PiVideoStream(resolution=self.resolution, framerate=10).start()
        self.terminate_flag = False
        self.start_flag = False
        self.real_age = None
        self.age_statue = None
        self.frame = None
        self.recognition = True
        self.rect = None
        self.process_this_frame = True

    def terminate(self):

        self.terminate_flag = True

    def run(self):

        while True:

            if self.terminate_flag:
                break

            frame = self.vs.read()
            time.sleep(0.01)
            if self.start_flag:
                if self.age_statue is None:
                    cv2.putText(frame, "Checking Document", (50, 250), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 255, 0),
                                2)
                    self.window.show_frame(frame)

                image = frame.copy()
                height, width = frame.shape[:2]
                if self.rect is None:

                    faces = detect_face_haar(frame=image)

                    for face in faces:

                        left, top, right, bottom = face

                        s_x = max(0, left - FACE_MARGIN)
                        e_x = min(width, right + FACE_MARGIN)
                        s_y = max(0, top - FACE_MARGIN)
                        e_y = min(height, bottom + FACE_MARGIN)
                        crop_face = frame[s_y:e_y, s_x:e_x]

                        self.window.card_face_image = crop_face

                        # ------- recognize card info(birthday) from frame ----
                        if self.frame is None:
                            self.frame = frame
                            self.rect = (left, top, right, bottom)
                else:
                    cv2.rectangle(image, (self.rect[0], self.rect[1]), (self.rect[2], self.rect[3]), (0, 255, 0), 2)
                    self.recognize_card(image=frame, face_right=self.rect[2])

                    # --------- send frame  --------------
                cv2.putText(image, self.window.document_type, (50, 50), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 255, 0), 2)
                self.window.show_frame(image)

            if not self.start_flag:
                if self.window.document_type == "Please Select Document Type":
                    cv2.putText(frame, self.window.document_type, (50, 250), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 255, 0),
                                2)
                    self.window.show_frame(frame)

                time.sleep(0.05)

    def recognize_card(self, image, face_right):
        try:
            date = extract_birthday(img=image, id_type=self.window.document_type, base_line=face_right)
            date = date.replace(".", "")

            if date != "":
                birth_year = 0
                if self.window.document_type == ID_TYPE[1] or self.window.document_type == ID_TYPE[2]:
                    birth_year = int(date[-4:])
                if self.window.document_type == ID_TYPE[0]:
                    birth_year = 1900 + int(date[-2:])
                    date = date.replace(date[-2:], birth_year)
                birth_month = int(date[2:4])
                birth_day = int(date[0:2])

                init_real_age = int(datetime.date.today().year) - birth_year
                current_month = datetime.date.today().month
                current_day = datetime.date.today().day

                if current_month >= birth_month:
                    if current_day >= birth_day:
                        real_age = init_real_age
                    else:
                        real_age = init_real_age - 1
                else:
                    real_age = init_real_age - 1
                self.real_age = real_age
                if self.real_age >= 18:
                    self.age_statue = "Allow"
                else:
                    self.age_statue = "Not Allow"
                self.window.show_recognition_result(date, self.real_age, self.age_statue)
                self.start_flag = False

        except Exception as e:
            log_print(info_str=e)
            pass

        time.sleep(0.01)


if __name__ == '__main__':
    CardRecognitionThread(win="").run()
