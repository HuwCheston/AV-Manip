import cv2
import threading
from numpy import zeros, uint8


class KeyThread:
    def __init__(self, params: dict, stop_event: threading.Event,):
        self.blank_image = zeros(shape=[100, 100, 3], dtype=uint8)
        keypress_manager = threading.Thread(target=self.main_loop, args=(stop_event, params))
        keypress_manager.start()

        # There is no need for the keypress manager to start at the same time as the video/audio recording - so there is
        # no use of the global_barrier to block it, as there was with the other threads.

    def main_loop(self, stop_event, params):
        cv2.namedWindow('Keypress Manager', cv2.WINDOW_NORMAL)
        while True:
            cv2.setWindowProperty('Keypress Manager', cv2.WND_PROP_TOPMOST, 1)  # Keep the keypress manager on top
            cv2.imshow('Keypress Manager', self.blank_image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('1'):
                params['flipped'] = True
            if key == ord('2'):
                params['delayed'] = True
            if key == ord('r'):
                for param in params.keys():
                    params[param] = False
            if key == ord('q'):
                break
        stop_event.set()    # This sets the stop_event for ALL other threads!
        cv2.destroyWindow('Keypress Manager')
