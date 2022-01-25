from cv2 import cv2
import threading
from numpy import zeros, uint8


class KeyThread:
    def __init__(self, params: dict, stop_event: threading.Event,):
        self.blank_image = zeros(shape=[100, 100, 3], dtype=uint8)  # Blank image for keypress manager to display
        self.name = 'Keypress Manager'
        keypress_manager = threading.Thread(target=self.start_keymanager, args=(stop_event, params))
        keypress_manager.start()

    def start_keymanager(self, stop_event, params):
        self.cv2_setup()
        self.main_loop(stop_event, params)
        self.exit_loop()

    def cv2_setup(self):
        cv2.namedWindow(self.name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.name, cv2.WND_PROP_TOPMOST, 1)  # Keep the keypress manager on top

    def main_loop(self, stop_event, params):
        while not stop_event.is_set():
            cv2.imshow(self.name, self.blank_image)
            # Detects keypresses to trigger modifications in CamThread and ReaThread
            key = chr(cv2.waitKey(1) % 255)
            match key:
                case '1':
                    params['flipped'] = True
                case '2':
                    params['delayed'] = True
                case '3':
                    print('Manipulation 3 (not yet implemented)')
                case '4':
                    print('Manipulation 4 (not yet implemented)')
                case 'r':
                    for param in params.keys():
                        params[param] = False
                    params['reset'] = True
                case 'q':
                    stop_event.set()

    def exit_loop(self):
        cv2.destroyWindow(self.name)
