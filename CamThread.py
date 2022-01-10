import cv2
import threading
import queue
import ffmpeg
import time
from collections import deque
import get_filename


class CamThread:
    def __init__(self, source: int, stop_event: threading.Event, global_barrier: threading.Barrier, params):

        self.camera_queue = queue.Queue(maxsize=5)
        self.edit_camera_queue = queue.Queue(maxsize=5)
        local_barrier = threading.Barrier(4)

        self.camera_reader = threading.Thread(target=camera_reader,
                                              args=(source,
                                                    self.camera_queue,
                                                    self.edit_camera_queue,
                                                    local_barrier,
                                                    stop_event,
                                                    global_barrier))
        self.camera_display = threading.Thread(target=camera_display,
                                               args=(source,
                                                     self.camera_queue,
                                                     local_barrier,
                                                     stop_event,
                                                     global_barrier))
        self.edit_camera_display = threading.Thread(target=edit_camera_display,
                                                    args=(source,
                                                          self.edit_camera_queue,
                                                          local_barrier,
                                                          params,
                                                          stop_event,
                                                          global_barrier))
        self.camera_recorder = threading.Thread(target=write_video,
                                                args=(source,
                                                      local_barrier,
                                                      stop_event,
                                                      global_barrier))

        self.camera_reader.start()
        self.camera_display.start()
        self.edit_camera_display.start()
        self.camera_recorder.start()


def camera_reader(source, camera_queue, edit_camera_queue, local_barrier, stop_event, global_barrier):
    cam = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    _, frame = cam.read()
    camera_queue.put(frame)
    edit_camera_queue.put(frame)
    print(f"Cam {source + 1} reader currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
    local_barrier.wait()
    global_barrier.wait()

    while not stop_event.is_set():
        _, frame = cam.read()
        camera_queue.put(frame)
        edit_camera_queue.put(frame)
    cam.release()


def camera_display(source, camera_queue, local_barrier, stop_event, global_barrier):
    name = f"Cam {source + 1} Rec"
    while True:
        try:
            frame = camera_queue.get(False)
        except queue.Empty:
            pass
        else:
            cv2.imshow(name, frame)
            break
    local_barrier.wait()

    print(f"Cam {source + 1} display currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
    global_barrier.wait()

    while not stop_event.is_set():
        frame = camera_queue.get()
        cv2.imshow(name, frame)
        cv2.waitKey(1)
    time.sleep(1)  # Wait for 1 sec to allow cv2 and ffmpeg time to stop
    cv2.destroyWindow(name)


def edit_camera_display(source, edit_camera_queue, local_barrier, edit_params: dict, stop_event, global_barrier):
    name = f"Cam {source + 1} View"
    while True:
        try:
            frame = edit_camera_queue.get(False)
        except queue.Empty:
            pass
        else:
            cv2.imshow(name, frame)
            break
    local_barrier.wait()

    print(f"Cam {source + 1} edit display currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
    global_barrier.wait()

    frames = deque(maxlen=150)
    while not stop_event.is_set():
        frame = edit_camera_queue.get()
        frames.append(frame)
        if edit_params['flipped']:
            frame = cv2.flip(frame, 0)
        if edit_params['delayed']:
            frame = frames[1]
        cv2.imshow(name, frame)
        cv2.waitKey(1)
    time.sleep(1)   # Wait for 1 sec to allow cv2 and ffmpeg time to stop
    cv2.destroyWindow(name)


def write_video(source, local_barrier, stop_event, global_barrier):
    name = f"Cam {source + 1} Rec"
    local_barrier.wait()

    process = (ffmpeg.input(format='gdigrab', framerate=30, filename=f"title={name}", loglevel='warning', )
               .output(preset="ultrafast", filename=f"./output/video/{name} Output.mkv",)
               .overwrite_output())
    print(f"Cam {source + 1} writer currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
    global_barrier.wait()

    process = process.run_async(pipe_stdin=True)

    while not stop_event.is_set():
        time.sleep(0.1)       # running this (rather than pass) in the loop increases performance
    process.communicate(str.encode( "q"))
    process.terminate()
