import threading
import time
import numpy as np
import cv2
import dlib
import keras
import face_recognition

from keras.utils.generic_utils import CustomObjectScope
from utils.folder_file_manager import log_print
from settings import LANDMARK_MODEL_PATH, LANDMARK_TXT_PATH, AGE_MODEL_PATH


class RecognitionThread(threading.Thread):
    def __init__(self, parent, params):

        threading.Thread.__init__(self)

        self.terminated = False
        self.stopped_flag = False

        self.check_db_flag = False

        print("Initializing recognition thread...")
        self.parent = parent

        # Initialize aligners for face alignment.
        self.aligner = dlib.shape_predictor(LANDMARK_MODEL_PATH)
        self.aligner_targets = np.loadtxt(LANDMARK_TXT_PATH)

        # Initialize networks for Age
        with CustomObjectScope({'relu6': keras.layers.ReLU(6.),
                                'DepthwiseConv2D': keras.layers.DepthwiseConv2D}):
            self.age_net = keras.models.load_model(AGE_MODEL_PATH)
            self.age_net._make_predict_function()

        self.minDetections = int(params.get("recognition", "min_detections"))
        self.minDetections = int(params.get("recognition", "min_detections"))

        # Starting the thread
        print("Recognition thread started...")

    @staticmethod
    def estimate_rigid_transform(landmarks, aligner_targets):

        first_idx = 27
        b_land = aligner_targets[first_idx:, :]
        landmarks = landmarks[first_idx:]
        a_land = np.hstack((np.array(landmarks), np.ones((len(landmarks), 1))))

        a = np.row_stack((np.array([-a_land[0][1], -a_land[0][0], 0, -1]), np.array([
            a_land[0][0], -a_land[0][1], 1, 0])))
        b = np.row_stack((-b_land[0][1], b_land[0][0]))

        for j in range(a_land.shape[0] - 1):
            j += 1
            a = np.row_stack((a, np.array([-a_land[j][1], -a_land[j][0], 0, -1])))
            a = np.row_stack((a, np.array([a_land[j][0], -a_land[j][1], 1, 0])))
            b = np.row_stack((b, np.array([[-b_land[j][1]], [b_land[j][0]]])))
        x_, res, rank, s = np.linalg.lstsq(a, b, rcond=-1)
        cos = (x_[0][0]).real.astype(np.float32)
        sin = (x_[1][0]).real.astype(np.float32)
        t_x = (x_[2][0]).real.astype(np.float32)
        t_y = (x_[3][0]).real.astype(np.float32)

        h_ = np.array([[cos, -sin, t_x], [sin, cos, t_y]])
        s = np.linalg.eigvals(h_[:, :-1])
        r_ = s.max(initial=None) / s.min(initial=None)

        return h_, r_

    @staticmethod
    def crop_face(img, rect, margin=0.2):
        x1 = rect.left()
        x2 = rect.right()
        y1 = rect.top()
        y2 = rect.bottom()

        # size of face
        w = x2 - x1 + 1
        h = y2 - y1 + 1

        # add margin
        full_crop_x1 = x1 - int(w * margin)
        full_crop_y1 = y1 - int(h * margin)
        full_crop_x2 = x2 + int(w * margin)
        full_crop_y2 = y2 + int(h * margin)

        # size of face with margin
        new_size_w = full_crop_x2 - full_crop_x1 + 1
        new_size_h = full_crop_y2 - full_crop_y1 + 1

        # ensure that the region cropped from the original image with margin
        # doesn't go beyond the image size
        crop_x1 = max(full_crop_x1, 0)
        crop_y1 = max(full_crop_y1, 0)
        crop_x2 = min(full_crop_x2, img.shape[1] - 1)
        crop_y2 = min(full_crop_y2, img.shape[0] - 1)

        # size of the actual region being cropped from the original image
        crop_size_w = crop_x2 - crop_x1 + 1
        crop_size_h = crop_y2 - crop_y1 + 1

        # coordinates of region taken out of the original image in the new image
        new_location_x1 = crop_x1 - full_crop_x1
        new_location_y1 = crop_y1 - full_crop_y1
        new_location_x2 = crop_x1 - full_crop_x1 + crop_size_w - 1
        new_location_y2 = crop_y1 - full_crop_y1 + crop_size_h - 1

        new_img = np.random.randint(256, size=(new_size_h, new_size_w, img.shape[2])).astype('uint8')
        new_img[new_location_y1: new_location_y2 + 1, new_location_x1: new_location_x2 + 1, :] = \
            img[crop_y1:crop_y2 + 1, crop_x1:crop_x2 + 1, :]

        # if margin goes beyond the size of the image, repeat last row of pixels
        if new_location_y1 > 0:
            new_img[0:new_location_y1, :, :] = np.tile(new_img[new_location_y1, :, :], (new_location_y1, 1, 1))

        if new_location_y2 < new_size_h - 1:
            new_img[new_location_y2 + 1:new_size_h, :, :] = np.tile(new_img[new_location_y2:new_location_y2 + 1, :, :],
                                                                    (new_size_h - new_location_y2 - 1, 1, 1))
        if new_location_x1 > 0:
            new_img[:, 0:new_location_x1, :] = np.tile(new_img[:, new_location_x1:new_location_x1 + 1, :],
                                                       (1, new_location_x1, 1))
        if new_location_x2 < new_size_w - 1:
            new_img[:, new_location_x2 + 1:new_size_w, :] = np.tile(new_img[:, new_location_x2:new_location_x2 + 1, :],
                                                                    (1, new_size_w - new_location_x2 - 1, 1))

        return new_img

    @staticmethod
    def preprocess_input(img):

        # Expected input is BGR
        x = img - img.min()
        x = 255.0 * x / x.max()

        x[..., 0] -= 103.939
        x[..., 1] -= 116.779
        x[..., 2] -= 123.68
        return x

    def terminate(self):
        self.terminated = True

    def check_face_from_db(self, face_img):
        try:
            from src.database.manager import DatabaseManager
            person_face_encoding = face_recognition.face_encodings(face_img)[0]

            records = DatabaseManager().select_info_from_db()
            print("records", records)
            db_face_encoding_list = []
            db_face_statue_list = []
            db_face_date_list = []

            if records.__len__() > 0:
                for record in records:
                    encoding = np.array(record[3].split(" "), dtype=float)
                    db_face_encoding_list.append(encoding)
                    db_face_statue_list.append(record[2])
                    db_face_date_list.append(record[1])
                print("record success")

                matches = face_recognition.compare_faces(db_face_encoding_list, person_face_encoding)
                print(matches)
                if True in matches:
                    print("Faces match.")
                    match_index = matches.index(True)
                    saved_statue = db_face_statue_list[match_index]
                    saved_date = db_face_date_list[match_index]

                    self.parent.db_saved_date = saved_date
                    self.parent.db_saved_statue = saved_statue
                    self.parent.stop_flag = True
                    if saved_statue == "allow":
                        self.parent.message = "[Erlaubt!]"
                    else:
                        self.parent.message = "[Nicht erlaubt!]"

                    self.parent.age_guessed_time = time.time()
                else:
                    print("Faces not match.")
                    self.check_db_flag = True
            else:
                print("There is no saved face encoding in db")
                self.check_db_flag = True

        except Exception as e:
            print("Failed checking database, it is face encoding problem")
            log_print(info_str=e)

    def run(self):

        while not self.parent.is_terminated() and not self.terminated:
            if self.stopped_flag:
                print("Age recog stopped")
                time.sleep(0.2)
            if not self.stopped_flag:
                # print("Age recog runing")
                faces = self.parent.get_faces()
                while faces is None:
                    time.sleep(0.1)
                    faces = self.parent.get_faces()

                valid_faces = [f for f in faces if len(f['bboxes']) > self.minDetections]

                for face in valid_faces:
                    # get the timestamp of the most recent frame:
                    timestamp = face['timestamps'][-1]
                    unit = self.parent.get_unit(self, timestamp)

                    if unit is not None:

                        if not self.check_db_flag:
                            img = unit.get_frame()
                            mean_box = np.mean(face['bboxes'], axis=0)
                            x, y, w, h = [int(c) for c in mean_box]
                            face_img = img[y:y + h, x:x + w]
                            self.check_face_from_db(face_img)

                        else:
                            img = unit.get_frame()
                            mean_box = np.mean(face['bboxes'], axis=0)
                            x, y, w, h = [int(c) for c in mean_box]

                            # Align the face to match the targets

                            # 1. DETECT LANDMARKS
                            dlib_box = dlib.rectangle(left=x, top=y, right=x + w, bottom=y + h)
                            dlib_img = img[..., ::-1].astype(np.uint8)

                            s = self.aligner(dlib_img, dlib_box)
                            landmarks = [[s.part(k).x, s.part(k).y] for k in range(s.num_parts)]

                            # 2. ALIGN
                            landmarks = np.array(landmarks)
                            m_rigid, r_rigid = self.estimate_rigid_transform(landmarks, self.aligner_targets)

                            if r_rigid < 1.5:
                                crop = cv2.warpAffine(img, m_rigid, (224, 224), borderMode=2)
                            else:
                                # Seems to distort too much, probably error in landmarks, then let's just crop.
                                crop = self.crop_face(dlib_img, dlib_box)
                                crop = cv2.resize(crop, (224, 224))
                            crop = crop.astype(np.float32)

                            # Recognize only if new face or every 5 rounds
                            if "age" not in face or face["recog_round"] % 5 == 0:
                                age_in = self.preprocess_input(crop)
                                time_start = time.time()
                                age_out = self.age_net.predict(np.expand_dims(age_in, 0))[0]
                                print("Age time: {:.2f} ms".format(1000 * (time.time() - time_start)))
                                age = np.dot(age_out, list(range(101)))
                                if "age" in face:
                                    face["age"] = 0.75 * face["age"] + 0.25 * age
                                else:
                                    face["age"] = age
                                    face["recog_round"] = 0
                            face["recog_round"] += 1
