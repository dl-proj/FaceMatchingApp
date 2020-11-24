import time


class GrabUnit:

    def __init__(self, frame):

        self.timestamp = time.time()
        self.detected = False
        self.age_recognized = False

        # Keep track of how many processes are accessing this unit        
        self.processes = 0
        self.frame = frame

    def get_times_stamp(self):

        return self.timestamp

    def get_frame(self):

        return self.frame

    def acquire(self):

        self.processes += 1

    def release(self):

        self.processes -= 1

    def is_free(self):

        if self.processes == 0:
            return True
        else:
            return False

    def get_num_processes(self):

        return self.processes

    def get_time_stamp(self):

        return self.timestamp

    def get_age(self):

        return time.time() - self.timestamp

    def set_detected(self):

        self.detected = True

    def set_age_recognized(self):

        self.age_recognized = True

    def is_detected(self):

        return self.detected

    def is_age_recognized(self):

        return self.age_recognized
