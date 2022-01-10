import queue
import threading
import time
import reapy
import cv2
import numpy as np
import ffmpeg
from collections import deque


class CamThread:
    def __init__(self, source: int, stop_event: threading.Event, global_barrier: threading.Barrier):

        self.camera_queue = queue.Queue(maxsize=5)
        self.edit_camera_queue = queue.Queue(maxsize=5)
        self.barrier = threading.Barrier(4)

        self.camera_reader = threading.Thread(target=camera_reader,
                                              args=(source,
                                                    self.camera_queue,
                                                    self.edit_camera_queue,
                                                    self.barrier,
                                                    stop_event,
                                                    global_barrier))
        self.camera_display = threading.Thread(target=camera_display,
                                               args=(source,
                                                     self.camera_queue,
                                                     self.barrier,
                                                     stop_event,
                                                     global_barrier))
        self.edit_camera_display = threading.Thread(target=edit_camera_display,
                                                    args=(source,
                                                          self.edit_camera_queue,
                                                          self.barrier,
                                                          params,
                                                          stop_event,
                                                          global_barrier))
        self.camera_recorder = threading.Thread(target=write_video,
                                                args=(source,
                                                      self.barrier,
                                                      stop_event,
                                                      global_barrier))

        self.camera_reader.start()
        self.camera_display.start()
        self.edit_camera_display.start()
        self.camera_recorder.start()


def camera_reader(source, camera_queue, edit_camera_queue, barrier, stop_event, global_barrier):
    print(f"Cam {source + 1} Loading...")
    cam = cv2.VideoCapture(source)
    _, frame = cam.read()
    camera_queue.put(frame)
    edit_camera_queue.put(frame)
    barrier.wait()
    global_barrier.wait()

    while not stop_event.is_set():
        _, frame = cam.read()
        camera_queue.put(frame)
        edit_camera_queue.put(frame)
    cam.release()


def camera_display(source, camera_queue, barrier, stop_event, global_barrier):
    name = f"Cam {source + 1} Rec"
    while True:
        try:
            frame = camera_queue.get(False)
        except queue.Empty:
            pass
        else:
            cv2.imshow(name, frame)
            break
    print(f'{name} ready!')
    barrier.wait()
    global_barrier.wait()

    while not stop_event.is_set():
        frame = camera_queue.get()
        cv2.imshow(name, frame)
        cv2.waitKey(1)
    cv2.destroyWindow(name)


def edit_camera_display(source, edit_camera_queue, barrier, edit_params: dict, stop_event, global_barrier):
    name = f"Cam {source + 1} View"
    while True:
        try:
            frame = edit_camera_queue.get(False)
        except queue.Empty:
            pass
        else:
            cv2.imshow(name, frame)
            break
    print(f'{name} ready!')
    barrier.wait()
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
    cv2.destroyWindow(name)


def write_video(source, barrier, stop_event, global_barrier):
    name = f"Cam {source + 1} Rec"

    process = (ffmpeg.input(format='gdigrab', framerate=30, filename=f"title={name}")
               .output(preset="ultrafast", filename=f"./FFMPEG Media/{name} Output.avi")
               .overwrite_output())
    barrier.wait()
    global_barrier.wait()
    process = process.run_async(pipe_stdin=True)

    while not stop_event.is_set():
        time.sleep(1)       # running this (rather than pass) in the loop increases performance
    process.communicate(str.encode("q"))
    process.terminate()


def keypress_manager(edit_params: dict, stop_event: threading.Event, global_barrier):
    blank_image = np.zeros(shape=[100, 100, 3], dtype=np.uint8)
    print('reached barrier')
    global_barrier.wait()

    while True:
        cv2.imshow('Keypress Manager', blank_image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('1'):
            edit_params['flipped'] = True
        if key == ord('2'):
            edit_params['delayed'] = True
        if key == ord('r'):
            for param in edit_params.keys():
                edit_params[param] = False
        if key == ord('q'):
            break
    stop_event.set()
    cv2.destroyWindow('Keypress Manager')


def reaper_manager(stop_event, global_barrier):
    project = reapy.Project()
    track = project.tracks[0]
    fx = track.fxs[0]
    global_barrier.wait()
    project.record()
    fx.enable()
    stop_event.wait()
    project.stop()


params = {
    'flipped': False,
    'delayed': False,
}

stopper = threading.Event()
GLOBAL_BARRIER = threading.Barrier(10)
manager = threading.Thread(target=keypress_manager, args=(params, stopper, GLOBAL_BARRIER))
rea_manager = threading.Thread(target=reaper_manager, args=(stopper, GLOBAL_BARRIER))

manager.start()
rea_manager.start()
camera1 = CamThread(source=0, stop_event=stopper, global_barrier=GLOBAL_BARRIER)
camera2 = CamThread(source=1, stop_event=stopper, global_barrier=GLOBAL_BARRIER)
