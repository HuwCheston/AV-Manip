import cv2
import threading
import numpy as np


class KeyMan:
    def __init__(self, edit_params: dict, stop_event: threading.Event,):
        self.blank_image = np.zeros(shape=[100, 100, 3], dtype=np.uint8)
        self.keypress_manager = threading.Thread(target=self.main_loop, args=(edit_params, stop_event))
        self.keypress_manager.start()

    def main_loop(self, edit_params, stop_event):
        while True:
            cv2.imshow('Keypress Manager', self.blank_image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('1'):
                edit_params['flipped'] = True
            if key == ord('2'):
                edit_params['delayed'] = True
            if key == ord('r'):
                for param in edit_params.keys():
                    edit_params[param] = False
            if key == ord('q'):
                break
        stop_event.set()
        cv2.destroyWindow('Keypress Manager')
