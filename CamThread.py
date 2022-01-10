import cv2
import threading
import queue
import ffmpeg
import time
from datetime import datetime
from collections import deque


class CamThread:
    def __init__(self, source: int, stop_event: threading.Event, global_barrier: threading.Barrier, params: dict):
        self.camera_queue = queue.Queue(maxsize=5)
        self.edit_camera_queue = queue.Queue(maxsize=5)
        self.local_barrier = threading.Barrier(4)
        self.source = source
        self.params = params

        methods = [self.camera_reader, self.camera_display, self.edit_camera_display, self.write_video]
        target_args = (stop_event, global_barrier)
        threads = [threading.Thread(target=method, args=target_args) for method in methods]
        for thread in threads:
            thread.start()

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

    def edit_camera_display(self, stop_event, global_barrier):
        name = f"Cam {self.source + 1} View"
        while True:
            try:
                frame = self.edit_camera_queue.get(False)
            except queue.Empty:
                pass
            else:
                cv2.imshow(name, frame)
                break
        frames = deque(maxlen=150)
        self.local_barrier.wait()

        print(f"Cam {self.source + 1} edit display currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        while not stop_event.is_set():
            frame = self.edit_camera_queue.get()
            frames.append(frame)
            if self.params['flipped']:
                frame = cv2.flip(frame, 0)
            if self.params['delayed']:
                frame = frames[1]
            cv2.imshow(name, frame)
            cv2.waitKey(1)
        time.sleep(1)   # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(name)

    def write_video(self, stop_event, global_barrier):
        winname = f"Cam {self.source + 1} Rec"
        filename = f'./output/video/{datetime.now().strftime("%d-%m-%y_%H.%M.%S")}_cam{self.source + 1}_out.mkv'
        self.local_barrier.wait()

        process = (ffmpeg.input(format='gdigrab', framerate="30", filename=f"title={winname}", loglevel='warning',)
                   .output(preset="ultrafast", filename=filename, qp="0", pix_fmt='yuv444p', video_size='1920x1080'))
        print(f"Cam {self.source + 1} writer currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        process = process.run_async(pipe_stdin=True)

        while not stop_event.is_set():
            time.sleep(0.1)       # running this (rather than pass) in the loop increases performance
        process.communicate(str.encode("q"))
        process.terminate()
