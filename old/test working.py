import queue
import threading
import time
import reapy
import cv2
import numpy as np
import ffmpeg
from collections import deque


class CamThread:
    def __init__(self, source: int, stop_event: threading.Event, lock_event=None):

        self.camera_queue = queue.Queue(maxsize=5)
        self.edit_camera_queue = queue.Queue(maxsize=5)
        self.barrier = threading.Barrier(2)

        self.camera_reader = threading.Thread(target=camera_reader,
                                              args=(source,
                                                    self.camera_queue,
                                                    self.edit_camera_queue,
                                                    self.barrier,
                                                    stop_event,
                                                    lock_event))
        self.camera_display = threading.Thread(target=camera_display,
                                               args=(source,
                                                     self.camera_queue,
                                                     self.barrier,
                                                     stop_event))
        self.edit_camera_display = threading.Thread(target=edit_camera_display,
                                                    args=(source,
                                                          self.edit_camera_queue,
                                                          self.barrier,
                                                          params,
                                                          stop_event))
        self.camera_recorder = threading.Thread(target=write_video,
                                                args=(source,
                                                      self.barrier,
                                                      stop_event))

        self.camera_reader.start()
        self.camera_display.start()
        self.edit_camera_display.start()
        self.camera_recorder.start()


def camera_reader(source, camera_queue, edit_camera_queue, barrier, stop_event, lock_event):
    print(f"Cam {source + 1} Loading...")
    cam = cv2.VideoCapture(source)
    _, frame = cam.read()
    camera_queue.put(frame)
    edit_camera_queue.put(frame)
    barrier.wait()

    # try:
    #     lock_event.set()
    # except AttributeError:
    #     pass

    while not stop_event.is_set():
        _, frame = cam.read()
        camera_queue.put(frame)
        edit_camera_queue.put(frame)
    cam.release()


def camera_display(source, camera_queue, barrier, stop_event):
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

    while not stop_event.is_set():
        frame = camera_queue.get()
        cv2.imshow(name, frame)
        cv2.waitKey(1)
    cv2.destroyWindow(name)


def edit_camera_display(source, edit_camera_queue, barrier, edit_params: dict, stop_event):
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


def write_video(source, barrier, stop_event):
    name = f"Cam {source + 1} Rec"
    barrier.wait()
    process = (ffmpeg.input(format='gdigrab', framerate=30, filename=f"title={name}")
               .output(preset="ultrafast", filename=f"./FFMPEG Media/{name} Output.avi")
               .overwrite_output())
    process = process.run_async(pipe_stdin=True)

    while not stop_event.is_set():
        time.sleep(1)       # running this (rather than pass) in the loop increases performance
    process.communicate(str.encode("q"))
    process.terminate()


def keypress_manager(edit_params: dict, stop_event: threading.Event, global_lock):
    global_lock.wait()
    print('lock released')
    blank_image = np.zeros(shape=[100, 100, 3], dtype=np.uint8)

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


def reaper_manager(stop_event, global_lock):
    project = reapy.Project()
    global_lock.wait()
    project.record()
    stop_event.wait()
    project.stop()


params = {
    'flipped': False,
    'delayed': False,
}

stopper = threading.Event()
global_barrier = threading.Barrier(10)

locker = threading.Event()
manager = threading.Thread(target=keypress_manager, args=(params, stopper, locker))
rea_manager = threading.Thread(target=reaper_manager, args=(stopper, locker))

manager.start()
rea_manager.start()
camera1 = CamThread(source=0, stop_event=stopper, lock_event=locker)
camera2 = CamThread(source=1, stop_event=stopper,)
