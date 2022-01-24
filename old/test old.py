import queue
import threading
import time

import cv2
import numpy as np
import ffmpeg


class CamThread:
    def __init__(self):

        # camera reader
        self.camera_queue = queue.Queue(maxsize=5)
        self.edit_camera_queue = queue.Queue(maxsize=5)

        camera_reader = threading.Thread(target=self.camera_reader)
        camera_display = threading.Thread(target=self.camera_display)
        edit_camera_display = threading.Thread(target=self.edit_camera_display)
        keypress_manager = threading.Thread(target=self.keypress_manager)
        camera_recorder = threading.Thread(target=self.write_video)

        self.stop_event = threading.Event()
        self.barrier = threading.Barrier(5)

        self.flipped = False
        self.delay = False

        camera_reader.start()
        camera_display.start()
        edit_camera_display.start()
        keypress_manager.start()
        camera_recorder.start()

    def camera_reader(self):
        print("Cam Loading...")
        cam = cv2.VideoCapture(0)
        _, frame = cam.read()
        self.camera_queue.put(frame)
        self.edit_camera_queue.put(frame)
        self.barrier.wait()

        while not self.stop_event.is_set():
            _, frame = cam.read()
            self.camera_queue.put(frame)
            self.edit_camera_queue.put(frame)

    def camera_display(self):
        print("doing something")
        while True:
            try:
                frame = self.camera_queue.get(False)
            except queue.Empty:
                pass
            else:
                cv2.imshow("frame", frame)
                break
        self.barrier.wait()

        while not self.stop_event.is_set():
            frame = self.camera_queue.get()
            cv2.imshow("frame", frame)
            cv2.waitKey(1)
        cv2.destroyWindow('frame')

    def edit_camera_display(self,):
        print("doing something else")
        while True:
            try:
                frame = self.edit_camera_queue.get(False)
            except queue.Empty:
                pass
            else:
                cv2.imshow("edit frame", frame)
                break
        self.barrier.wait()

        while not self.stop_event.is_set():
            frame = self.edit_camera_queue.get()
            if self.flipped:
                frame = cv2.flip(frame, 0)
            if self.delay:
                cv2.waitKey(50)
            cv2.imshow("edit frame", frame)
            cv2.waitKey(1)
        cv2.destroyWindow('edit frame')

    def keypress_manager(self):
        blank_image = np.zeros(shape=[100,100,3], dtype=np.uint8)
        self.barrier.wait()

        while True:
            cv2.imshow('Keypress Manager', blank_image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('a'):
                self.flipped = True
            if key == ord('s'):
                self.delay = True
            if key == ord('r'):
                self.flipped = False
                self.delay = False
            if key == ord('q'):
                break
        self.stop_event.set()
        cv2.destroyWindow('Keypress Manager')

    def write_video(self):
        self.barrier.wait()
        process = (ffmpeg.input(format='gdigrab', framerate=30, filename="title=frame")
                   .output(preset="ultrafast", filename="./FFMPEG Media/output.avi")
                   .overwrite_output())
        process = process.run_async(pipe_stdin=True)

        while not self.stop_event.is_set():
            time.sleep(1)
        process.communicate(str.encode("q"))
        process.terminate()


SM = CamThread()
