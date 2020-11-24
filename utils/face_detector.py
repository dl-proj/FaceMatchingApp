import cv2
import time

from settings import FACE_MODEL_HAAR_PATH


def detect_face_frozen(frame):

    frozen_graph = "/media/mensa/Entertainment/DemoTest/agecard/detection/ssd_mobilenetv1/" \
                   "frozen_inference_graph.pb"
    text_graph = "/media/mensa/Entertainment/DemoTest/agecard/detection/ssd_mobilenetv1/graph.pbtxt"
    cv_net = cv2.dnn.readNetFromTensorflow(frozen_graph, text_graph)

    rows, cols = frame.shape[0:2]
    cv_net.setInput(cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True, crop=False))
    cv_out = cv_net.forward()
    bboxes = []

    for detection in cv_out[0, 0, :, :]:
        score = float(detection[2])

        if score > 0.3:
            left = int(detection[3] * cols)
            top = int(detection[4] * rows)
            right = int(detection[5] * cols)
            bottom = int(detection[6] * rows)
            width = right - left
            height = bottom - top
            bboxes.append([left, top, width, height])

    return bboxes


def detect_face_haar(frame):

    front_detector = cv2.CascadeClassifier(FACE_MODEL_HAAR_PATH)
    faces = front_detector.detectMultiScale(frame, 1.3, 5)
    modified_faces = []
    for face in faces:
        x, y, w, h = face
        if w == 0 or h == 0:
            continue
        modified_faces.append([x, y, x + w, y + h])

    return modified_faces


if __name__ == '__main__':

    img_path = ""
    img = cv2.imread(img_path)
    rotate_img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    # cv2.imshow("origin frame", rotate_img)
    # cv2.waitKey()
    st_time = time.time()
    face_rects = detect_face_haar(frame=rotate_img)
    print("detection time:", time.time() - st_time)
    for rect in face_rects:
        f_left, f_top, f_right, f_bottom = rect
        cv2.rectangle(rotate_img, (f_left, f_top), (f_right, f_bottom), (0, 0, 255), 2)

    cv2.imshow("face image", cv2.resize(rotate_img, (800, 600)))
    cv2.waitKey()
