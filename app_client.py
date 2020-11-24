import configparser
import sys
import time
import cv2
import socket
import struct
import pickle
import scrollphathd as sphd
import threading

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from threading import Thread
from scrollphathd.fonts import font3x5
from gpiozero import LED
from src.client.card_recog_thread import CardRecognitionThread
from utils import led
from utils.folder_file_manager import log_print
from settings import ID_TYPE, CONFIG_FILE_PATH

red_led = LED(18)
yellow_led = LED(24)
green_led = LED(23)


def padding(s):
    return s + ((16 - len(s) % 16) * '`')


def remove_padding(s):
    return s.replace('`', '')


class CardSystem(Thread):
    def __init__(self, parameters, window):
        Thread.__init__(self)
        self.params = parameters
        self.window = window
        self.host = self.params.get("socket", "host")
        self.port = self.params.getint("socket", "port")

        self.check_yellow_thread = None
        self.connection = None
        self.terminate_flag = False
        self.send_card_recog_data_flag = False
        self.card_face_image = None
        self.card_recog_data = None

        self.send_data_time = None

        self.turn_on_red_flag = False
        self.turn_on_green_flag = False
        self.turn_on_yellow_flag = False

    def terminate(self):
        self.terminate_flag = True

    def check_server(self):
        print("\n[!] Checking server")
        while True:
            try:
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((self.host, self.port))
                print("\n[!] Server is running!")
                break
            except Exception as e:
                print("\n[!] Server is not running!")
                log_print(info_str=e)
                time.sleep(0.2)

    def check_yellow_status(self):
        st_time = time.time()
        time_interval = 0
        check_ret = False
        while time_interval < 10:
            if self.window.card_recognition_thread.start_flag:
                check_ret = True
                break
            time_interval = time.time() - st_time

        if not check_ret:
            self.window.cancel_btn_released()

    def send_face_image(self):
        ret_code, jpg_buffer = cv2.imencode(".jpg", self.card_face_image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        data = pickle.dumps(jpg_buffer, 0)
        size = len(data)

        self.connection.sendall(struct.pack(">L", size) + data)
        print(" Send one face image to Server System ")

    def turn_on_led(self):
        if self.turn_on_red_flag:
            red_led.on()
            print("red on")
        if self.turn_on_green_flag:
            green_led.on()
            print("green on")
        if self.turn_on_yellow_flag:
            yellow_led.on()
            print("yellow on")

    def turn_off_led(self):
        if self.turn_on_red_flag:
            red_led.off()
            self.turn_on_red_flag = False
        if self.turn_on_green_flag:
            green_led.off()
            self.turn_on_green_flag = False
        if self.turn_on_yellow_flag:
            print(self.turn_on_yellow_flag)
            yellow_led.off()
            self.turn_on_yellow_flag = False

    def turnoff_led(self):
        sphd.clear()

        red_led.off()
        self.turn_on_red_flag = False
        green_led.off()
        self.turn_on_green_flag = False
        yellow_led.off()
        self.turn_on_yellow_flag = False
        sphd.show()

    def show_red_string(self, message):
        sphd.clear()
        sphd.write_string(message, font=font3x5)
        while self.turn_on_red_flag:
            sphd.show()
            sphd.scroll(1)
            time.sleep(0.1)
        print("red")

    def show_green_string(self, message):
        sphd.clear()
        sphd.write_string('-' + message + '-', font=font3x5, brightness=0.5)
        # sphd.write_string(message)
        sphd.show()
        sphd.scroll(1)
        print("green")
        time.sleep(3)
        self.turnoff_led()
        # sphd.clear()
        # sphd.write_string('-', font=font3x5)
        # sphd.show()

    @staticmethod
    def show_yellow_string(message):
        sphd.clear()
        sphd.write_string(message, font=font3x5, brightness=0.5)
        sphd.show()
        sphd.scroll(1)
        time.sleep(0.1)
        # print('############################################### yellow')

    @staticmethod
    def scroll_message(message):  # for test
        sphd.clear()  # Clear the display and reset scrolling to (0, 0)
        length = sphd.write_string(message)  # Write out your message
        sphd.show()  # Show the result
        time.sleep(0.3)  # Initial delay before scrolling
        print("scroll")
        length -= sphd.width

        # Now for the scrolling loop...
        while length > 0:
            sphd.scroll(1)  # Scroll the buffer one place to the left
            sphd.show()  # Show the result
            length -= 1
            time.sleep(0.05)  # Delay for each scrolling step

        time.sleep(0.5)  # Delay at the end of scrolling

    def send_recog_data(self):
        if self.card_recog_data == "Allow":
            signal = "allow"
            self.connection.send(padding(signal).encode("utf-8"))
            self.send_face_image()
            # self.turnoff_leds()
            # self.turn_off_all()
        if self.card_recog_data == "Not Allow":
            signal = "not allow"
            self.connection.send(padding(signal).encode("utf-8"))
        if self.card_recog_data == "can not recog":
            print(self.card_recog_data)
            signal = "check yourself"
            # self.turnoff_leds()
            self.connection.send(padding(signal).encode("utf-8"))
            # self.turn_off_all()
            # self.turnoff_leds()
        self.send_data_time = time.time()

    def receive_data(self):
        signal = self.connection.recv(4096)
        signal = remove_padding(signal.decode("utf-8"))
        print(signal)
        cmd = signal.split(":")[0]
        # age = signal.split(":")[1]
        # win.get_event()
        # if cmd == "active card system":
        #    win.get_event()
        if cmd == "turn on red":
            # self.turn_off_LED()
            led.turn_on_red()
            self.turn_on_red_flag = True
            # self.turn_on_red()
            # self.turn_on_LED()
            # thread = threading.Thread(target=self.show_red_string, args="Alarm")
            # thread.setDaemon()
            # thread.start()
            # self.show_red_string("alarm")
        elif cmd == "turn on green":
            self.turn_off_led()
            self.turn_on_green_flag = True
            led.turn_on_green()
            # time.sleep(3)
            # self.turn_off_all()
            # print('##################################### turn off')
            # self.turn_on_LED()
            # self.show_green_string(age)
            # print ("=====================================", age)
            # sleep(3)
            # sphd.clear()
        elif cmd == "turn on yellow":
            # win.get_event()
            # self.turn_off_LED()
            if self.check_yellow_thread is not None:
                self.check_yellow_thread.join()
            self.turn_on_yellow_flag = True
            led.turn_on_yellow()
            print("turn on yellow")
            # self.turn_on_LED()
            self.window.get_event()
            self.check_yellow_thread = threading.Thread(target=self.check_yellow_status)
            self.check_yellow_thread.start()
            # thread = threading.Thread(target=self.show_yellow_string, args="Check")
            # thread.setDaemon()
            # thread.start()
            # self.show_yellow_string('check')

        else:
            print(" Server is running... ", signal)

    def send_data(self):
        if self.send_card_recog_data_flag:
            signal = "send recog result"
            self.connection.send(padding(signal).encode("utf-8"))
            time.sleep(0.2)
            self.send_recog_data()
            self.turn_off_led()
            self.send_card_recog_data_flag = False
            print("send recog data to age system!")
        else:
            signal = "card system is running"
            self.connection.send(padding(signal).encode("utf-8"))

    def run(self):
        self.check_server()
        # self.show_green_string('yes')
        # self.scroll_message('test')
        # signall = "turn on yellow"
        # win.get_event()
        while True:
            try:
                if self.terminate_flag:
                    print(self.terminate_flag)
                    break
                self.receive_data()
                self.send_data()
            except Exception as e:
                log_print(info_str=e)
                time.sleep(0.05)
                connected = False
                print(" ### Client Disconnected ")
                while not connected:
                    try:
                        self.check_server()
                        connected = True
                        print(" ### Client Reconnected")
                    except socket.error:
                        pass

            if self.send_data_time is not None:
                now = time.time()
                if now - self.send_data_time > 5:
                    self.window.show_init_screen()
                    self.send_data_time = None

            time.sleep(0.01)


class CardWindow(QtWidgets.QMainWindow):
    start_signal = pyqtSignal()

    def __init__(self, param):
        super(CardWindow, self).__init__()

        # ------ create card recognition thread and start ---------------
        self.params = param
        self.card_recognition_thread = CardRecognitionThread(self)
        self.card_recognition_thread.setDaemon(True)
        self.card_recognition_thread.start()

        # -----------------------------------------------------
        self.card_sys = CardSystem(self.params, self)
        self.card_sys.setDaemon(True)
        self.card_sys.start()
        # ------------------------------------------------------

        self.document_type = ""
        self.active_flag = False
        self.face_image = None

        self.card_recognized_flag = False
        self.card_face_image = None
        self.card_face_image_list = []
        self.card_real_age = None
        self.card_age_statue = None

        # self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        # ------ configuration card recog sub window --------------------
        self.setGeometry(50, 50, 800, 600)
        self.setStyleSheet("background-color: rgb(40,40,40)")

        self.camera_frame = QtWidgets.QLabel(self)
        self.camera_frame.setGeometry(100, 50, 600, 400)
        self.camera_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.camera_frame.setText(" Not Active ")
        self.camera_frame.setStyleSheet("background-color: rgb(50,50,70);\n"
                                         "color: rgb(0, 255, 0);\n"
                                         "font: 26pt \"MS Shell Dlg 2\";")

        self.card_label = QtWidgets.QLabel(self)
        self.card_label.setGeometry(100, 5, 300, 40)
        self.card_label.setText("Ausweiskontrolle:")
        self.card_label.setStyleSheet("color: rgb(250, 167, 8);\n"
                                      "font: 24pt \"MS Shell Dlg 2\";")

        self.cancel_btn = QtWidgets.QPushButton(self)
        self.cancel_btn.setText("Cancel")
        self.cancel_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                      "color: rgb(250, 167, 8);\n"
                                      "font: 16pt \"MS Shell Dlg 2\";"
                                      "border-style: outset;\n"
                                      "border-width: 2px;\n"
                                      "border-radius: 15px;\n")
        self.cancel_btn.setGeometry(690, 540, 100, 50)

        self.id_card_btn = QtWidgets.QPushButton(self)
        self.id_card_btn.setText(ID_TYPE[1])
        self.id_card_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                       "color: rgb(250, 167, 8);\n"
                                       "font: 16pt \"MS Shell Dlg 2\";"
                                       "border-style: outset;\n"
                                       "border-width: 2px;\n"
                                       "border-radius: 15px;\n")
        self.id_card_btn.setGeometry(100, 470, 150, 50)

        self.passport_btn = QtWidgets.QPushButton(self)
        self.passport_btn.setText(ID_TYPE[2])
        self.passport_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                        "color: rgb(250, 167, 8);\n"
                                        "font: 16pt \"MS Shell Dlg 2\";"
                                        "border-style: outset;\n"
                                        "border-width: 2px;\n"
                                        "border-radius: 15px;\n")
        self.passport_btn.setGeometry(325, 470, 150, 50)

        self.drive_license_btn = QtWidgets.QPushButton(self)
        self.drive_license_btn.setText(ID_TYPE[0])
        self.drive_license_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                             "color: rgb(250, 167, 8);\n"
                                             "font: 16pt \"MS Shell Dlg 2\";"
                                             "border-style: outset;\n"
                                             "border-width: 2px;\n"
                                             "border-radius: 15px;\n")
        self.drive_license_btn.setGeometry(550, 470, 150, 50)

        self.birth_label = QtWidgets.QLabel(self)
        self.birth_label.setGeometry(100, 460, 200, 40)
        self.birth_label.setText("Geburtsdatum:")
        self.birth_label.setStyleSheet("color: rgb(250, 167, 8);\n"
                                       "font: 20pt \"MS Shell Dlg 2\";")

        self.birth_value = QtWidgets.QLabel(self)
        self.birth_value.setGeometry(100, 510, 200, 50)
        self.birth_value.setAlignment(QtCore.Qt.AlignCenter)
        # self.birth_value.setText("27.08.1985")
        self.birth_value.setStyleSheet("color: rgb(0, 255, 0);\n"
                                       "font: 24pt \"MS Shell Dlg 2\";"
                                       "border-color: rgb(250, 167, 8);\n"
                                       "border-style: outset;\n"
                                       "border-width: 2px;\n"
                                       "border-radius: 15px;\n")

        self.age_label = QtWidgets.QLabel(self)
        self.age_label.setGeometry(340, 460, 100, 40)
        self.age_label.setText("Alter:")
        self.age_label.setStyleSheet("color: rgb(250, 167, 8);\n"
                                     "font: 20pt \"MS Shell Dlg 2\";")

        self.age_value = QtWidgets.QLabel(self)
        self.age_value.setGeometry(340, 510, 100, 50)
        self.age_value.setAlignment(QtCore.Qt.AlignCenter)
        # self.age_value.setText("34")
        self.age_value.setStyleSheet("color: rgb(0, 255, 0);\n"
                                     "font: 24pt \"MS Shell Dlg 2\";"
                                     "border-color: rgb(250, 167, 8);\n"
                                     "border-style: outset;\n"
                                     "border-width: 2px;\n"
                                     "border-radius: 15px;\n")

        self.statue_label = QtWidgets.QLabel(self)
        self.statue_label.setGeometry(480, 460, 100, 40)
        self.statue_label.setText("Staus:")
        self.statue_label.setStyleSheet("color: rgb(250, 167, 8);\n"
                                        "font: 20pt \"MS Shell Dlg 2\";")

        self.statue_value = QtWidgets.QLabel(self)
        self.statue_value.setGeometry(480, 510, 195, 50)
        self.statue_value.setAlignment(QtCore.Qt.AlignCenter)
        # self.statue_value.setText("Not Allow")
        self.statue_value.setStyleSheet("color: rgb(0, 255, 0);\n"
                                        "font: 23pt \"MS Shell Dlg 2\";"
                                        "border-color: rgb(250, 167, 8);\n"
                                        "border-style: outset;\n"
                                        "border-width: 2px;\n"
                                        "border-radius: 15px;\n")

        self.setFixedSize(800, 600)

        # ------- connect signals of buttons to slots -------
        self.cancel_btn.pressed.connect(self.cancel_btn_pressed)
        self.id_card_btn.pressed.connect(self.id_card_btn_pressed)
        self.passport_btn.pressed.connect(self.passport_btn_pressed)
        self.drive_license_btn.pressed.connect(self.drive_license_btn_pressed)

        self.cancel_btn.released.connect(self.cancel_btn_released)
        self.id_card_btn.released.connect(self.id_card_btn_released)
        self.passport_btn.released.connect(self.passport_btn_released)
        self.drive_license_btn.released.connect(self.drive_license_btn_released)

        self.start_signal.connect(self.show_selection_buttons)

        self.hide_selection_buttons()
        self.hide_controls()

        # self.showFullScreen()
        # self.get_event()

    def show_init_screen(self):
        self.camera_frame.setText(" Not Active ")
        self.camera_frame.setStyleSheet("background-color: rgb(50,50,70);\n"
                                         "color: rgb(0, 255, 0);\n"
                                         "font: 26pt \"MS Shell Dlg 2\";")
        self.document_type = ""
        self.birth_value.clear()
        self.age_value.clear()
        self.statue_value.clear()
        # self.start_signal.disconnect()
        self.hide_controls()
        self.hide_selection_buttons()

    def hide_selection_buttons(self):
        self.id_card_btn.hide()
        self.passport_btn.hide()
        self.drive_license_btn.hide()

    def hide_controls(self):
        self.birth_label.hide()
        self.birth_value.hide()
        self.age_label.hide()
        self.age_value.hide()
        self.statue_label.hide()
        self.statue_value.hide()

    def show_selection_buttons(self):
        self.id_card_btn.show()
        self.passport_btn.show()
        self.drive_license_btn.show()

    def show_controls(self):
        self.birth_label.show()
        self.birth_value.show()
        self.age_label.show()
        self.age_value.show()
        self.statue_label.show()
        self.statue_value.show()

    def get_event(self):
        # self.cammeraframe.setText(" Please Select Document Type ")
        self.document_type = "Please Select Document Type"
        self.start_signal.emit()

    def cancel_btn_pressed(self):
        self.cancel_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                      "color: rgb(250, 167, 8);\n"
                                      "font: 14pt \"MS Shell Dlg 2\";"
                                      "border-style: outset;\n"
                                      "border-width: 2px;\n"
                                      "border-radius: 12px;\n")
        self.cancel_btn.setGeometry(695, 545, 90, 40)

    def cancel_btn_released(self):
        self.card_recognition_thread.start_flag = False
        self.cancel_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                      "color: rgb(250, 167, 8);\n"
                                      "font: 16pt \"MS Shell Dlg 2\";"
                                      "border-style: outset;\n"
                                      "border-width: 2px;\n"
                                      "border-radius: 15px;\n")
        self.cancel_btn.setGeometry(690, 540, 100, 50)

        self.birth_value.setText("?")
        self.age_value.setText("?")
        self.statue_value.setText("Cann't Recog")

        self.card_sys.send_card_recog_data_flag = True
        self.card_sys.card_recog_data = "can not recog"
        led.turn_off_all()
        print('######################## cancel')

    def id_card_btn_pressed(self):
        self.id_card_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                       "color: rgb(250, 167, 8);\n"
                                       "font: 14pt \"MS Shell Dlg 2\";"
                                       "border-style: outset;\n"
                                       "border-width: 2px;\n"
                                       "border-radius: 12px;\n")
        self.id_card_btn.setGeometry(105, 475, 140, 40)

    def id_card_btn_released(self):
        self.id_card_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                       "color: rgb(250, 167, 8);\n"
                                       "font: 16pt \"MS Shell Dlg 2\";"
                                       "border-style: outset;\n"
                                       "border-width: 2px;\n"
                                       "border-radius: 15px;\n")
        self.id_card_btn.setGeometry(100, 470, 150, 50)
        self.card_recognition_thread.start_flag = True
        self.document_type = ID_TYPE[1]
        self.hide_selection_buttons()
        self.show_controls()

    def passport_btn_pressed(self):
        self.passport_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                        "color: rgb(250, 167, 8);\n"
                                        "font: 14pt \"MS Shell Dlg 2\";"
                                        "border-style: outset;\n"
                                        "border-width: 2px;\n"
                                        "border-radius: 12px;\n")
        self.passport_btn.setGeometry(330, 475, 140, 40)

    def passport_btn_released(self):
        self.passport_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                        "color: rgb(250, 167, 8);\n"
                                        "font: 16pt \"MS Shell Dlg 2\";"
                                        "border-style: outset;\n"
                                        "border-width: 2px;\n"
                                        "border-radius: 15px;\n")
        self.passport_btn.setGeometry(325, 470, 150, 50)
        self.card_recognition_thread.start_flag = True
        self.document_type = ID_TYPE[2]
        self.hide_selection_buttons()
        self.show_controls()

    def drive_license_btn_pressed(self):
        self.drive_license_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                             "color: rgb(250, 167, 8);\n"
                                             "font: 14pt \"MS Shell Dlg 2\";"
                                             "border-style: outset;\n"
                                             "border-width: 2px;\n"
                                             "border-radius: 12px;\n")
        self.drive_license_btn.setGeometry(555, 475, 140, 40)

    def drive_license_btn_released(self):
        self.drive_license_btn.setStyleSheet("background-color: rgb(30,30,30);\n"
                                             "color: rgb(250, 167, 8);\n"
                                             "font: 16pt \"MS Shell Dlg 2\";"
                                             "border-style: outset;\n"
                                             "border-width: 2px;\n"
                                             "border-radius: 15px;\n")
        self.drive_license_btn.setGeometry(550, 470, 150, 50)
        self.card_recognition_thread.start_flag = True
        self.document_type = ID_TYPE[0]
        self.hide_selection_buttons()
        self.show_controls()

    def show_frame(self, frame):
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (600, 400))
            img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(img)
            self.camera_frame.setPixmap(pix)

    def show_recognition_result(self, birth, age, statue):
        try:
            birth = birth.replace(",", ".")
        except Exception as e:
            log_print(info_str=e)
            pass
        self.birth_value.setText(birth)
        self.age_value.setText(str(age))
        self.statue_value.setText(statue)

        self.card_sys.send_card_recog_data_flag = True
        self.card_sys.card_recog_data = statue
        self.card_sys.card_face_image = self.card_face_image


if __name__ == "__main__":

    params = configparser.ConfigParser()
    params.read(CONFIG_FILE_PATH)

    app = QtWidgets.QApplication(sys.argv)
    win = CardWindow(params)
    win.show()
    # win.get_event()
    sys.exit(app.exec_())
