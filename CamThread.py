import threading
import ffmpeg
import time
import os
import numpy as np
from cv2 import cv2
from queue import Queue, Empty
from datetime import datetime
from collections import deque
# TODO: investigate using PyTest here!


class CamThread:
    def __init__(self, source: int, stop_event: threading.Event, global_barrier: threading.Barrier, params: dict):
        self.source = source
        self.params = params
        self.queue_length = 128  # This can be changed to save memory if required
        self.researcher_cam_queue = Queue(maxsize=self.queue_length)
        self.performer_cam_queue = Queue(maxsize=self.queue_length)
        self.global_barrier = global_barrier
        self.stop_event = stop_event
        self.start_threads(self.thread_init())

    def thread_init(self):
        # Define threads and thread arguments
        classes = [CamRead(source=self.source, perfor_q=self.performer_cam_queue, resear_q=self.researcher_cam_queue),
                   ResearcherCamView(source=self.source, queue=self.researcher_cam_queue),
                   PerformerCamView(source=self.source, queue=self.performer_cam_queue, params=self.params),
                   CamWrite(source=self.source)]
        args = (self.global_barrier, self.stop_event)
        threads = [threading.Thread(target=cl.start_cam, args=args) for cl in classes]
        return threads

    @staticmethod
    def start_threads(thread_list):
        for thread in thread_list:
            thread.start()


class CamRead:
    def __init__(self, source, resear_q, perfor_q):
        self.source = source
        self.cam = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        self.researcher_cam_queue = resear_q
        self.performer_cam_queue = perfor_q

    def start_cam(self, global_barrier, stop_event):
        self.read_frame()
        self.wait(global_barrier)
        self.main_loop(stop_event)
        self.exit_loop()

    def read_frame(self):
        _, frame = self.cam.read()
        if frame is None:
            print('no frame!')
            os._exit(1)
        else:
            self.researcher_cam_queue.put(frame)
            self.performer_cam_queue.put(frame)

    def wait(self, global_barrier):
        print(f"Cam {self.source + 1} reader currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

    def main_loop(self, stop_event):
        while not stop_event.is_set():
            _, frame = self.cam.read()
            self.researcher_cam_queue.put(frame)
            self.performer_cam_queue.put(frame)

    def exit_loop(self):
        self.cam.release()


class ResearcherCamView:
    def __init__(self, source: int, queue: Queue):
        self.name = f"Cam {source + 1} Rec"
        self.queue = queue

    def start_cam(self, global_barrier, stop_event):
        initialise_camera(n=self.name, q=self.queue)
        self.wait(global_barrier)
        self.main_loop(stop_event)
        self.exit_loop()

    def wait(self, global_barrier):
        print(f"{self.name} currently waiting. Waiting threads = {global_barrier.n_waiting + 1}\n")
        global_barrier.wait()

    def main_loop(self, stop_event):
        while not stop_event.is_set():
            # Acquire frame from queue
            frame = self.queue.get()
            cv2.imshow(self.name, frame)
            cv2.waitKey(1)

    def exit_loop(self):
        time.sleep(1)  # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(self.name)


class PerformerCamView:
    def __init__(self, source: int, queue: Queue, params: dict):
        self.name = f"Cam {source + 1} View"
        self.queue = queue
        self.params = params

    def start_cam(self, global_barrier, stop_event):
        initialise_camera(n=self.name, q=self.queue)
        self.wait(global_barrier)
        self.main_loop(stop_event)
        self.exit_loop()

    def wait(self, global_barrier):
        print(f"{self.name} currently waiting. Waiting threads = {global_barrier.n_waiting + 1}\n")
        global_barrier.wait()

    def main_loop(self, stop_event):
        fps = 30
        delay_frames = deque(maxlen=round((fps*(self.params['*max delay time']/1000))))

        loop_params = {
            "frames": [],
            "var": 0,
            "has_loop": False,
        }

        cascade = cv2.CascadeClassifier(r".\venv\Lib\site-packages\opencv_python-4.5.5.62.dist-info\lbpcascade_frontalface_improved.xml")
        scale_factor = 1.4
        dim = 60
        detected_face = ()

        while not stop_event.is_set():
            frame = self.queue.get()
            delay_frames.append(frame)  # Frames are always added to the deque so they can be played later (for delay)

            # Modify frame
            match self.params:
                case {'flipped': True}:
                    frame = cv2.flip(frame, 0)

                case {'delayed': True}:
                    frame = delay_frames[-round(fps*(self.params['*delay time']/1000))]

                # TODO: This logic works, but I think it could be better...
                case {'loop rec': True}:
                    if loop_params["has_loop"]:
                        loop_params["var"] = 0
                        loop_params["frames"].clear()
                        loop_params["has_loop"] = False
                    loop_params["frames"].append(frame)

                case {'loop play': True}:
                    if loop_params["var"] >= len(loop_params["frames"]):
                        loop_params["var"] = 0
                    frame = loop_params["frames"][loop_params["var"]]
                    loop_params["var"] += 1

                case {'loop clear': True}:
                    loop_params["var"] = 0
                    loop_params["frames"].clear()

                case {'blanked': True}:
                    frame, detected_face = self._manip_blank_region(cascade, detected_face, dim, frame, scale_factor)

                case {'*reset': True}:
                    if len(loop_params["frames"]) > 0:
                        loop_params["var"] = 0
                        loop_params["has_loop"] = True
                    self.params['*reset lock'].release()

            # cv2.moveWindow(self.name, -1500, 0)   # Comment this out to display on 2nd monitor
            frame = cv2.resize(frame, (0, 0), fx=2.0, fy=2.0)
            cv2.imshow(self.name, frame)
            cv2.waitKey(1)

    def _manip_blank_region(self, cascade, detection, dim, frame, scale_factor):
        regions = cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), scale_factor, 4)
        if isinstance(regions, np.ndarray):
            for (x, y, w, h) in regions:
                cv2.rectangle(frame, (x - dim, y - dim), (x + w + dim, y + h + dim), (0, 0, 0), -1)
                detection = (x, y, w, h)
        else:
            try:
                (x, y, w, h) = detection
            except ValueError:
                pass
            else:
                cv2.rectangle(frame, (x - dim, y - dim), (x + w + dim, y + h + dim), (0, 0, 0), -1)
        return frame, detection

    def exit_loop(self):
        time.sleep(1)  # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(self.name)


class CamWrite:
    # If you run into FileNotFound errors when importing ffmpeg-python, make sure that ffmpeg.exe is placed in the
    # Python/Scripts directory of your environment.
    def __init__(self, source: int):
        self.source = source
        self.window_name = f"Cam {self.source + 1} Rec"
        self.filename = f'output/video/{datetime.now().strftime("%d-%m-%y_%H.%M.%S")}_cam{self.source + 1}_out.avi'

    def start_cam(self, global_barrier, stop_event):
        self.wait(global_barrier)
        # TODO: fix ffmpeg flags to ensure highest quality of output
        process = (
            ffmpeg.input(format='gdigrab', framerate="30", filename=f"title={self.window_name}", loglevel='warning',
                         probesize='500M')
            .output(filename=self.filename, pix_fmt='yuv420p', video_size='1920x1080'))
        self.main_loop(stop_event, process)
        self.exit_loop()

    def wait(self, global_barrier):
        print(f"Cam {self.source + 1} Writer currently waiting. Waiting threads = {global_barrier.n_waiting + 1}\n")
        global_barrier.wait()

    @staticmethod
    def main_loop(stop_event, process):
        running_process = process.run_async(pipe_stdin=True)
        while not stop_event.is_set():
            time.sleep(0.1)  # running this (rather than pass) in the loop increases performance
        running_process.communicate(str.encode("q"))  # Send quit command to ffmpeg process
        running_process.terminate()

    def exit_loop(self):
        # Print stats about the video file
        get_video_stats(self.filename)


def initialise_camera(n: str, q: Queue) -> None:
    while True:
        try:
            frame = q.get(False)
        except Empty:
            time.sleep(1)
        else:
            cv2.imshow(n, frame)
            break
    return


def get_video_stats(filename):
    # TODO: implement this function (as a separate file?)
    vid = cv2.VideoCapture(filename)
    fps = vid.get(cv2.CAP_PROP_FPS)
    framecount = vid.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = framecount / fps
    print(duration)
