import configparser
import face_recognition
import cv2
import socket
import struct
import pickle
import time

from src.server.age_main_thread import AgeGuessingMainThread
from utils.folder_file_manager import log_print


def padding(s):
    return s + ((16 - len(s) % 16) * '`')


def remove_padding(s):
    return s.replace('`', '')


class AgeSystem:

    def __init__(self, parameters):

        self.params = parameters
        self.host = self.params.get("socket", "host")
        self.port = self.params.getint("socket", "port")
        self.connection = None

        self.terminate_flag = False
        self.send_active_signal_flag = False
        self.send_red_signal_flag = False
        self.send_green_signal_flag = False
        self.send_yellow_signal_flag = False

        self.calc_age = 0

        self.card_face_image = None
        self.person_face_image_list = []

        self.age_guess_thread = AgeGuessingMainThread(self.params, self)
        self.age_guess_thread.setDaemon(True)
        self.age_guess_thread.start()

    def terminate(self):
        self.terminate_flag = True

    def socket_connection(self):
        tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_server.bind((self.host, self.port))
        print(" listening client's request ")
        tcp_server.listen(1)

        (self.connection, (ip, port)) = tcp_server.accept()
        print(" accept client's request ")

    def get_card_sys_result(self):
        signal = self.connection.recv(4096)
        signal = remove_padding(signal.decode("utf-8"))
        print(signal)
        if signal == "allow":
            data = b""
            payload_size = struct.calcsize(">L")

            while len(data) < payload_size:
                data += self.connection.recv(4096)

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]

            while len(data) < msg_size:
                data += self.connection.recv(4096)
            frame_data = data[:msg_size]

            image = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            self.card_face_image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            self.face_compare()
            print(" Receive one face image from Card system ")
        if signal == "not allow":
            self.age_guess_thread.message = "[Nicht erlaubt!]"
            self.age_guess_thread.age_guessed_time = time.time()
        if signal == "check yourself":
            self.age_guess_thread.message = "[Check Yourself!]"
            self.age_guess_thread.age_guessed_time = time.time()

    def face_compare(self):
        try:
            from src.database.manager import DatabaseManager
            face_encoding1 = None
            for i in range(0, self.person_face_image_list.__len__()):
                try:
                    face_encoding1 = face_recognition.face_encodings(self.person_face_image_list[i])[0]
                    break
                except Exception as e:
                    log_print(info_str=e)
                    print("can't find face feature from image")

            face_locations = face_recognition.face_locations(self.card_face_image)
            face_encoding2 = face_recognition.face_encodings(self.card_face_image, face_locations)

            matches = face_recognition.compare_faces(face_encoding2, face_encoding1)
            print(matches)
            if True in matches:
                print("Faces match.")
                self.age_guess_thread.message = "[Erlaubt!]"
                self.age_guess_thread.age_guessed_time = time.time()

                DatabaseManager().save_face_encoding_to_db(face_encoding1, "allow")
            else:
                print("Faces not match.")
                self.age_guess_thread.message = "[Nicht erlaubt!]"
                self.age_guess_thread.age_guessed_time = time.time()

                DatabaseManager().save_face_encoding_to_db(face_encoding1, "not allow")
            self.person_face_image_list = []
        except Exception as e:
            print("Faces not captured or can't not find features from face images!")
            log_print(info_str=e)

    def receive_data(self):
        signal = self.connection.recv(4096)
        print(signal)
        signal = remove_padding(signal.decode("utf-8"))
        if signal == "send recog result":
            print("receive card recog result")
            self.get_card_sys_result()
        else:
            print(" Client is running... ", signal)

    def send_data(self):
        if self.send_active_signal_flag:
            signal = "active card system"
            self.send_active_signal_flag = False
        if self.send_red_signal_flag:
            signal = "turn on red:null"
            self.send_red_signal_flag = False
        elif self.send_green_signal_flag:
            signal = "turn on green:" + str(self.calc_age)
            self.send_green_signal_flag = False
        elif self.send_yellow_signal_flag:
            signal = "turn on yellow:null"
            self.send_yellow_signal_flag = False
        else:
            signal = "check running:null"
        self.connection.send(padding(signal).encode("utf-8"))

    def main(self):
        self.socket_connection()
        while True:
            try:
                if self.terminate_flag:
                    break
                self.send_data()
                self.receive_data()

            except Exception as e:
                log_print(info_str=e)
                time.sleep(0.5)
                connected = False
                print(" Client Disconnected ")
                while not connected:
                    try:
                        self.socket_connection()
                        connected = True
                        print(" Client Reconnected")
                    except socket.error:
                        pass
            time.sleep(0.2)


if __name__ == "__main__":
    paramFile = "config.ini"
    params = configparser.ConfigParser()
    params.read(paramFile)

    age_sys = AgeSystem(params)
    age_sys.main()
