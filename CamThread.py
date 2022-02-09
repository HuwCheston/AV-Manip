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
        self.queue_length = 64  # This can be changed to save memory if required
        self.researcher_cam_queue = Queue(maxsize=self.queue_length)
        self.performer_cam_queue = Queue(maxsize=self.queue_length)
        self.global_barrier = global_barrier
        self.stop_event = stop_event
        self.start_threads(self.thread_init())

    def thread_init(self):
        # Define threads and thread arguments
        classes = [CamRead(source=self.source, perfor_q=self.performer_cam_queue,
                           resear_q=self.researcher_cam_queue, params=self.params),
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
    def __init__(self, source, params, resear_q, perfor_q):
        self.source = source
        self.cam = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        self.researcher_cam_queue = resear_q
        self.performer_cam_queue = perfor_q
        self.params = params
        self.config_cam()

    def start_cam(self, global_barrier, stop_event):
        self.read_frame()
        self.wait(global_barrier)
        self.main_loop(stop_event)
        self.exit_loop()

    def config_cam(self):
        # Set the FPS
        # Change of FPS may require restart of program due to threading...
        # TODO: check and make sure this doesn't break anything!
        self.cam.set(cv2.CAP_PROP_FPS, self.params["*fps"])
        self.params["*fps"] = round(self.cam.get(cv2.CAP_PROP_FPS))

        # Set the resolution
        res = self.params['*resolution'].split('x')
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, float(res[0]))
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, float(res[1]))
        self.params['*resolution'] = f'{round(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))}x' \
                                     f'{round(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))}'

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
        delay_frames = deque(maxlen=round(self.params['*fps']*(self.params['*max delay time']/1000)))
        loop_params = self.params['*loop params']

        # TODO: refactor these into UserParams.py somehow - they're taking up a lot of space here.
        cascade_location = r".\venv\Lib\site-packages\opencv_python-4.5.5.62.dist-info"
        blank_params = {
            "face": {
                "cascade": cv2.CascadeClassifier(fr'{cascade_location}\lbpcascade_frontalface_improved.xml'),
                "scaleFactor": 1.4,
                "minNeighbors": 4,
                "dimensions": 60,
                "previous_detection": np.full((1, 4), fill_value=100),
                "minNum": 1
            },
            "eye": {
                "cascade": cv2.CascadeClassifier(fr'{cascade_location}\haarcascade_eye_tree_eyeglasses.xml'),
                "scaleFactor": 2.7,
                "minNeighbors": 3,
                "dimensions": 1,
                "previous_detection": np.full((2, 4), fill_value=100),   # Make sure fill - dimensions > 0!
                "minNum": 2,
            }
        }

        while not stop_event.is_set():
            frame = self.queue.get()
            delay_frames.append(frame)  # Frames are always added to the deque so they can be played later (for delay)

            # Modify frame
            match self.params:
                case {'flipped': True}:
                    frame = cv2.flip(frame, 0)  # This is a test manip and probably won't be used

                case {'delayed': True}:
                    # TODO: Need to catch errors here if delayed time is outside recorded range
                    # Out-of-sync delay is likely a performance issue (e.g. overheating laptop!)
                    frame = delay_frames[-round(self.params['*fps']*(self.params['*delay time']/1000))]

                case {'loop rec': True}:
                    self._manip_loop_rec(frame, loop_params)

                case {'loop play': True}:
                    frame = self._manip_loop_play(loop_params)

                case {'loop clear': True}:
                    loop_params["var"] = 0
                    loop_params["frames"].clear()

                case {'pause video': True} | {'pause both': True}:
                    if self.params['*pause frame'] is None:
                        self.params['*pause frame'] = frame
                    frame = self.params['*pause frame']

                case {'blank face': True}:
                    self._manip_detect_blanked_region(frame, params=blank_params["face"])

                case {'blank eyes': True}:
                    # TODO: implement error correction if only one eye detected (i'm lazy and this is hard)
                    self._manip_detect_blanked_region(frame, params=blank_params['eye'])

                case {'*reset video': True}:
                    self._reset_manips(loop_params, blank_params)

            # cv2.moveWindow(self.name, -1500, 0)   # Comment this out to display on 2nd monitor
            frame = cv2.resize(frame, (0, 0), fx=self.params['*scaling'], fy=self.params['*scaling'])
            cv2.imshow(self.name, frame)
            cv2.waitKey(1)

    def exit_loop(self):
        time.sleep(1)  # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(self.name)

    def _manip_loop_rec(self, frame, params):
        if params["has_loop"]:
            params["var"] = 0
            params["frames"].clear()
            params["has_loop"] = False
        params["frames"].append(frame)

    def _manip_loop_play(self, params):
        if params["var"] >= len(params["frames"]):
            params["var"] = 0
        frame = params["frames"][params["var"]]
        params["var"] += 1
        return frame

    def _manip_detect_blanked_region(self, frame, params):
        regions = params["cascade"].detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                                     params["scaleFactor"], params["minNeighbors"])
        if len(regions) == params["minNum"]:
            params["previous_detection"] = regions
        else:
            regions = params["previous_detection"]
        for region in regions:
            self._manip_plot_blanked_region(frame, params, region)

    def _manip_plot_blanked_region(self, frame, params, region):
        try:
            (x, y, w, h) = region
        except ValueError:
            pass
        else:
            cv2.rectangle(frame, (x - params["dimensions"], y - params["dimensions"]),
                          (x + w + params["dimensions"], y + h + params["dimensions"]), (0, 0, 0), -1)

    def _reset_manips(self, loop_params, blank_params):
        # TODO: this could look a bit nicer i'm sure
        loop_params["var"] = 0
        loop_params["has_loop"] = True
        self.params['*pause frame'] = None
        blank_params['face']['previous_detection'] = np.full((1, 4), fill_value=100)
        blank_params['eye']['previous_detection'] = np.full((1, 4), fill_value=100)
        self.params['*reset video'] = False


class CamWrite:
    # If you run into FileNotFound errors when importing ffmpeg-python, make sure that ffmpeg.exe is placed in the
    # Python/Scripts directory of your environment.

    def __init__(self, source: int):
        self.source = source
        self.window_name = f"Cam {self.source + 1} Rec"
        self.filename = f'output/video/{datetime.now().strftime("%d-%m-%y_%H.%M.%S")}_cam{self.source + 1}_out.avi'

    def start_cam(self, global_barrier, stop_event):
        # On high-resolution monitors, gdigrab may not display black padding around the captured video. I'd suggest
        # changing your monitor display resolution if this is an issue, as I can't find a workaround in ffmpeg.

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
            time.sleep(0.1)  # running this (rather than pass) in the loop improves performance
        running_process.communicate(str.encode("q"))  # Send quit command to ffmpeg process
        running_process.terminate()

    def exit_loop(self):
        # Print stats about the video file
        # TODO: implement this function (as a separate file?)
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
    vid = cv2.VideoCapture(filename)
    fps = vid.get(cv2.CAP_PROP_FPS)     # TODO: this should use user_params['*fps'] instead, I think
    framecount = vid.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = framecount / fps
    print(duration)
