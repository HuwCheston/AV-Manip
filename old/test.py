import cv2
from vidgear.gears import CamGear, WriteGear
import threading
import reapy
import time
import keyboard

project = reapy.Project()


class CamThread(threading.Thread):
    def __init__(self, preview_name, cam_id):
        threading.Thread.__init__(self)
        self.previewName = preview_name
        self.camID = cam_id


    def run(self):
        print("Starting " + self.previewName)
        cam_preview(self.previewName, self.camID)


def cam_preview(preview_name, cam_id):
    start_time = time.time()
    print(f'{preview_name} starting...')

    # cv2.namedWindow(preview_name)
    # cam = cv2.VideoCapture(cam_id)
    # cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    # cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cam.set(cv2.CAP_PROP_BUFFERSIZE, 2)
    # cam.set(cv2.CAP_PROP_FPS, 30)

    cam = CamGear(source=cam_id).start_thread()
    writer = WriteGear(output_filename='vidgear_out.mp4')

    # fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
    # out = cv2.VideoWriter(f'{preview_name}_output_30fps.avi', fourcc, cam.get(cv2.CAP_PROP_FPS), (1280, 720))
    #
    # if cam.isOpened():
    #     frame = cam.read()
    # else:
    #     rval = False

    end_time = time.time()
    print(f'{preview_name} now running! Took {round(end_time - start_time, 2)} seconds.')
    barrier.wait()
    barrier.reset()
    if cam_id == 0:
        project.record()
    barrier.wait()

    while not thread_exit.is_set():
        frame = cam.read()
        cv2.imshow(preview_name, frame)
        writer.write(frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    thread_exit.set()
    project.stop()
    writer.close()
    cv2.destroyAllWindows()
    cam.stop()
    print('Exiting...')


# def keypress_handler():
#     while True:
#         if keyboard.is_pressed('q'):
#             project.stop()
#             thread_exit.set()
#             print('Exiting...')
#             break


# Create threads as follows
thread1 = CamThread("Camera 1", 0)
# thread2 = CamThread("Camera 2", 1)
# thread3 = CamThread

barrier = threading.Barrier(1)
thread_exit = threading.Event()

thread1.start()
# stop_thread = threading.Thread(target=keypress_handler())
# stop_thread.run()
# thread2.start()
# thread3.start()
