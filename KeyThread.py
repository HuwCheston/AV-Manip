import cv2
import threading
from numpy import zeros, uint8


class KeyThread:
    def __init__(self, params: dict, stop_event: threading.Event,):
        self.blank_image = zeros(shape=[100, 100, 3], dtype=uint8)  # Blank image for keypress manager to display

        # Define threads
        keypress_manager = threading.Thread(target=self.main_loop, args=(stop_event, params))
        keypress_manager.start()

    def main_loop(self, stop_event, params):
        """
        Creates a new CV2 window, listens for keypresses, sends these to KeyThread/CamThread to trigger manipulations.
        """
        # Initialisation
        cv2.namedWindow('Keypress Manager', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Keypress Manager', cv2.WND_PROP_TOPMOST, 1)  # Keep the keypress manager on top


        # Wait for other threads to initialise
        # There is no need for the keypress manager to start at the same time as the video/audio recording - so there is
        # no use of the global_barrier to block it while the other threads initialise, as with CamThread and ReaThread

        # Main loop
        while not stop_event.is_set():
            cv2.imshow('Keypress Manager', self.blank_image)

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
                case 'q':
                    stop_event.set()

        # Exit loop, cleanup and close thread
        cv2.destroyWindow('Keypress Manager')
