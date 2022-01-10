import cv2
import threading
import queue
import ffmpeg
import time
from collections import deque


class CamThread:
    def __init__(self, source: int, stop_event: threading.Event, global_barrier: threading.Barrier, params: dict):
        self.camera_queue = queue.Queue(maxsize=5)
        self.edit_camera_queue = queue.Queue(maxsize=5)
        self.local_barrier = threading.Barrier(4)
        self.source = source

        camera_reader = threading.Thread(target=self.camera_reader, args=(stop_event, global_barrier))
        camera_display = threading.Thread(target=self.camera_display, args=(stop_event, global_barrier))
        edit_camera_display = threading.Thread(target=self.edit_camera_display, args=(stop_event, global_barrier, params))
        camera_recorder = threading.Thread(target=self.write_video, args=(stop_event, global_barrier))

        camera_reader.start()
        camera_display.start()
        edit_camera_display.start()
        camera_recorder.start()

    def camera_reader(self, stop_event, global_barrier):
        cam = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        _, frame = cam.read()
        self.camera_queue.put(frame)
        self.edit_camera_queue.put(frame)
        print(f"Cam {self.source + 1} reader currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        self.local_barrier.wait()
        global_barrier.wait()

        while not stop_event.is_set():
            _, frame = cam.read()
            self.camera_queue.put(frame)
            self.edit_camera_queue.put(frame)
        cam.release()

    def camera_display(self, stop_event, global_barrier):
        name = f"Cam {self.source + 1} Rec"
        while True:
            try:
                frame = self.camera_queue.get(False)
            except queue.Empty:
                pass
            else:
                cv2.imshow(name, frame)
                break
        self.local_barrier.wait()

        print(f"Cam {self.source + 1} display currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        while not stop_event.is_set():
            frame = self.camera_queue.get()
            cv2.imshow(name, frame)
            cv2.waitKey(1)
        time.sleep(1)  # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(name)

    def edit_camera_display(self, stop_event, global_barrier, params):
        name = f"Cam {self.source + 1} View"
        while True:
            try:
                frame = self.edit_camera_queue.get(False)
            except queue.Empty:
                pass
            else:
                cv2.imshow(name, frame)
                break
        self.local_barrier.wait()

        print(f"Cam {self.source + 1} edit display currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        frames = deque(maxlen=150)
        while not stop_event.is_set():
            frame = self.edit_camera_queue.get()
            frames.append(frame)
            if params['flipped']:
                frame = cv2.flip(frame, 0)
            if params['delayed']:
                frame = frames[1]
            cv2.imshow(name, frame)
            cv2.waitKey(1)
        time.sleep(1)   # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(name)

    def write_video(self, stop_event, global_barrier):
        name = f"Cam {self.source + 1} Rec"
        self.local_barrier.wait()

        process = (ffmpeg.input(format='gdigrab', framerate=30, filename=f"title={name}", loglevel='warning', )
                   .output(preset="ultrafast", filename=f"./output/video/{name} Output.mkv",)
                   .overwrite_output())
        print(f"Cam {self.source + 1} writer currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        process = process.run_async(pipe_stdin=True)

        while not stop_event.is_set():
            time.sleep(0.1)       # running this (rather than pass) in the loop increases performance
        process.communicate(str.encode("q"))
        process.terminate()
