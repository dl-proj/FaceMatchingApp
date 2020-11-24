import threading

from src.server.face_detection_thread import FaceDetectionThread
from src.server.age_recognition_thread import RecognitionThread


class UnitServer:

    def __init__(self, maxUnits=4):

        self.maxUnits = maxUnits
        self.units = []
        self.mutex = threading.Lock()

    def get_unit(self, caller, timestamp=None):

        self.mutex.acquire()

        # Detection thread will receive the newest undetected frame

        unit = None
        if timestamp is not None:

            for f in self.units:
                if f.get_time_stamp() == timestamp:
                    unit = f
        else:
            if isinstance(caller, FaceDetectionThread):
                valid_units = [f for f in self.units if not f.is_detected()]
                if len(valid_units) == 0:
                    unit = None
                else:
                    unit = valid_units[-1]
                    unit.acquire()
                    unit.set_detected()

            # Age thread will receive the newest detected frame with age rec not done

            if isinstance(caller, RecognitionThread):
                valid_units = [f for f in self.units if f.is_detected() and not f.is_age_recognized()]
                if len(valid_units) == 0:
                    unit = None
                else:
                    unit = valid_units[-1]
                    unit.acquire()
                    unit.set_detected()
        self.mutex.release()

        return unit

    def put_unit(self, unit):

        self.mutex.acquire()

        if len(self.units) >= self.maxUnits:
            # Attempt to remove oldest unit
            if self.units[0].is_free():
                self.units.pop(0)

        if len(self.units) < self.maxUnits:
            self.units.append(unit)
        else:
            print("Unable to add new unit.")

        self.mutex.release()
