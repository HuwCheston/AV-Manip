import cv2
import threading
import queue
import ffmpeg
import time
import os
from datetime import datetime
from collections import deque

# TODO: Refactor this into a group of four classes, all created by the CamThread. Each class should have the same
#  initialise/wait/loop functions, but split into different methods.

# TODO: investigate using PyTest here!
class CamThread:
    def __init__(self, source: int, stop_event: threading.Event, global_barrier: threading.Barrier, params: dict):
        # TODO: Queu and Barrier objects here have 'magic' numbers as parameters - use len(methods) etc.
        # Define class attributes
        self.researcher_cam_queue = queue.Queue(maxsize=5)
        self.performer_cam_queue = queue.Queue(maxsize=5)
        self.local_barrier = threading.Barrier(4)
        self.source = source
        self.params = params

        # Define threads and thread arguments
        methods = [self.camera_reader, self.display_researcher_camera, self.display_performer_camera, self.write_video]
        target_args = (stop_event, global_barrier)
        threads = [threading.Thread(target=method, args=target_args) for method in methods]

        # Start threads
        for thread in threads:
            thread.start()

    def camera_reader(self, stop_event, global_barrier):
        """
        Grabs frame from USB camera source, puts to researcher/performer cam queue.
        """
        # Initialisation
        cam = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        _, frame = cam.read()
        if frame is None:
            print('no frame!')
            os._exit(1)
        else:
            self.researcher_cam_queue.put(frame)
            self.performer_cam_queue.put(frame)

        # Wait for other threads to initialise
        print(f"Cam {self.source + 1} reader currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        self.local_barrier.wait()
        global_barrier.wait()

        # Main loop
        while not stop_event.is_set():
            # Read frame from webcam
            _, frame = cam.read()

            # Put frame in queue for modification and viewing
            self.researcher_cam_queue.put(frame)
            self.performer_cam_queue.put(frame)

        # Exit loop, cleanup and close thread
        cam.release()

    def display_researcher_camera(self, stop_event, global_barrier):
        """
        Grabs frame from researcher camera queue and displays it (without any manipulations).
        """
        # Initialisation
        name = f"Cam {self.source + 1} Rec"
        initialise_camera(n=name, q=self.researcher_cam_queue)

        # Wait for other threads to complete initialisation
        self.local_barrier.wait()
        print(f"Cam {self.source + 1} display currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        # Main loop
        while not stop_event.is_set():
            # Acquire frame from queue
            frame = self.researcher_cam_queue.get()

            # Show frame
            cv2.imshow(name, frame)
            cv2.waitKey(1)

        # Exit loop, cleanup and close thread
        time.sleep(1)  # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(name)

    def display_performer_camera(self, stop_event, global_barrier):
        """
        Grabs frame from performer camera queue and displays it (with manipulations, if triggered by KeyThread).
        """
        # Initialisation
        name = f"Cam {self.source + 1} View"
        frames = deque(maxlen=150)
        initialise_camera(n=name, q=self.performer_cam_queue)

        # Wait for other threads to complete initialisation
        self.local_barrier.wait()
        print(f"Cam {self.source + 1} edit display currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        # Main loop
        while not stop_event.is_set():
            # Acquire frame from queue
            frame = self.performer_cam_queue.get()
            frames.append(frame)    # Frames are added to the deque so they can be played later (for delay effect)

            # Modify frame
            if self.params['flipped']:
                frame = cv2.flip(frame, 0)
            if self.params['delayed']:
                frame = frames[1]

            # Show modified frame
            cv2.imshow(name, frame)
            cv2.waitKey(1)

        # Exit loop, cleanup and close thread
        time.sleep(1)   # Wait for 1 sec to allow cv2 and ffmpeg time to stop
        cv2.destroyWindow(name)

    def write_video(self, stop_event, global_barrier):
        """
        Initialises FFmpeg process to record researcher camera stream and save it in ./output/video
        """
        # Initialisation
        winname = f"Cam {self.source + 1} Rec"
        filename = f'./output/video/{datetime.now().strftime("%d-%m-%y_%H.%M.%S")}_cam{self.source + 1}_out.avi'
        self.local_barrier.wait()
        process = (ffmpeg.input(format='gdigrab', framerate="30", filename=f"title={winname}", loglevel='warning',)
                   .output(filename=filename, pix_fmt='yuv420p', video_size='1920x1080'))
        # TODO: fix ffmpeg flags to ensure highest quality of output

        # Wait for other threads to complete initialisation
        print(f"Cam {self.source + 1} writer currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        # Main loop
        process = process.run_async(pipe_stdin=True)
        while not stop_event.is_set():
            time.sleep(0.1)       # running this (rather than pass) in the loop increases performance

        # Exit loop, cleanup and close thread
        process.communicate(str.encode("q"))    # Send quit command to ffmpeg process
        process.terminate()

        # Print stats about the video file
        get_video_stats(filename)


def initialise_camera(n: str, q: queue.Queue) -> None:
    while True:
        try:
            frame = q.get(False)
        except queue.Empty:
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
