import os

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(CUR_DIR, 'database', 'face_db.db')
FACE_MODEL_HAAR_PATH = os.path.join(CUR_DIR, 'models', 'face', 'haarcascade_frontalface_default.xml')
AGE_MODEL_PATH = os.path.join(CUR_DIR, 'models', 'age', 'model.h5')
LANDMARK_MODEL_PATH = os.path.join(CUR_DIR, 'models', 'face', 'shape_predictor_68_face_landmarks.dat')
LANDMARK_TXT_PATH = os.path.join(CUR_DIR, 'models', 'face', 'targets_symm.txt')
CONFIG_FILE_PATH = os.path.join(CUR_DIR, 'config.ini')

OCR_THRESH_VALUE = 106
CONFIRM_FRAME_RATE = 60
FACE_MARGIN = 40
GRADIENT = 0
ID_TOP = 0.4
ID_BOTTOM = 0.8
ID_LEFT = 1
CHARACTER_HEIGHT_THRESH = (1 / 50)

COUNTRY_NAME = "DEUTSCH"
ID_TYPE = ["Drive License", "ID Card", "Passport"]
