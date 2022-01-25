from cv2 import cv2
import threading
import ffmpeg
import time
import os
from queue import Queue, Empty
from datetime import datetime
from collections import deque

# If you run into FileNotFound errors when importing ffmpeg-python, make sure that ffmpeg.exe is placed in the
# Python/Scripts directory of your environment.

# TODO: Refactor this into a group of four classes, all created by the CamThread. Each class should have the same
#  initialise/wait/loop functions, but split into different methods.

# TODO: investigate using PyTest here!


class CamThread:
    def __init__(self, source: int, stop_event: threading.Event, global_barrier: threading.Barrier, params: dict):

        self.source = source
        self.params = params
        self.queue_length = 128  # This can be changed to save memory if required
        self.researcher_cam_queue = Queue(maxsize=self.queue_length)
        self.performer_cam_queue = Queue(maxsize=self.queue_length)

        # Define threads and thread arguments
        classes = [CamRead(source=self.source, performer_cam_queue=self.performer_cam_queue, researcher_cam_queue=self.researcher_cam_queue),
                   ResearcherCamView(source=self.source, queue=self.researcher_cam_queue),
                   PerformerCamView(source=self.source, queue=self.performer_cam_queue, params=self.params),
                   CamWrite(source=self.source)]
        # FIXME: local barrier needs fixing (is it necessary?)
        local_barrier = threading.Barrier(1)
        args = (local_barrier, global_barrier, stop_event)
        self.threads = [threading.Thread(target=cl.start_cam, args=args) for cl in classes]
        self.start_threads()

    def start_threads(self):
        for thread in self.threads:
            thread.start()


class CamRead:
    def __init__(self, source, researcher_cam_queue, performer_cam_queue):
        self.source = source
        self.cam = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        self.researcher_cam_queue = researcher_cam_queue
        self.performer_cam_queue = performer_cam_queue

    def start_cam(self, local_barrier, global_barrier, stop_event):
        self.read_frame()
        self.wait(local_barrier, global_barrier)
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

    def wait(self, global_barrier, local_barrier):
        print(f"Cam {self.source + 1} reader currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        local_barrier.wait()
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

    def start_cam(self, local_barrier, global_barrier, stop_event):
        initialise_camera(n=self.name, q=self.queue)
        self.wait(local_barrier, global_barrier)
        self.main_loop(stop_event)
        self.exit_loop()

    def wait(self, local_barrier, global_barrier):
        local_barrier.wait()
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

    def start_cam(self, local_barrier, global_barrier, stop_event):
        initialise_camera(n=self.name, q=self.queue)
        self.wait(local_barrier, global_barrier)
        self.main_loop(stop_event)
        self.exit_loop()

    def wait(self, local_barrier, global_barrier):
        local_barrier.wait()
        print(f"{self.name} currently waiting. Waiting threads = {global_barrier.n_waiting + 1}\n")
        global_barrier.wait()

    def main_loop(self, stop_event):
        # TODO: fix this 'magic number'
        frames = deque(maxlen=150)
        while not stop_event.is_set():
            frame = self.queue.get()
            frames.append(frame)  # Frames are added to the deque so they can be played later (for delay effect)

            # TODO: replace this with match - case syntax (see KeyThread)
            # Modify frame
            if self.params['flipped']:
                frame = cv2.flip(frame, 0)
            if self.params['delayed']:
                frame = frames[1]

            cv2.imshow(self.name, frame)
            cv2.waitKey(1)

    def exit_loop(self):
        time.sleep(1)  # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(self.name)


class CamWrite:
    def __init__(self, source: int):
        self.source = source
        self.window_name = f"Cam {self.source + 1} Rec"
        self.filename = f'output/video/{datetime.now().strftime("%d-%m-%y_%H.%M.%S")}_cam{self.source + 1}_out.avi'
        # TODO: fix ffmpeg flags to ensure highest quality of output

    def start_cam(self, local_barrier, global_barrier, stop_event):
        print('cam write running on latest version')
        self.wait(local_barrier, global_barrier)
        process = (
            ffmpeg.input(format='gdigrab', framerate="30", filename=f"title={self.window_name}", loglevel='warning',
                         probesize='500M')
            .output(filename=self.filename, pix_fmt='yuv420p', video_size='1920x1080'))
        self.main_loop(stop_event, process)
        self.exit_loop()

    def wait(self, local_barrier, global_barrier):
        local_barrier.wait()
        print(f"Cam {self.source + 1} Writer currently waiting. Waiting threads = {global_barrier.n_waiting + 1}\n")
        global_barrier.wait()

    def main_loop(self, stop_event, process):
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
    # TODO: implement this function
    vid = cv2.VideoCapture(filename)
    fps = vid.get(cv2.CAP_PROP_FPS)
    framecount = vid.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = framecount / fps
    print(duration)