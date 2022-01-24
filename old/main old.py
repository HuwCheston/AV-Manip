# import required libraries
import threading
import cv2
import reapy
import time
import ffmpeg


def write_video():
    barrier.wait()
    process = (ffmpeg.input(format='gdigrab', framerate=30, filename="title=Record Frame")
               .output(preset="ultrafast", filename="./FFMPEG Media/output_THISONE.avi")
               .overwrite_output())
    process = process.run_async(pipe_stdin=True)
    while not stop_event.is_set():
        pass
    process.communicate(str.encode("q"))
    process.terminate()


def capture_video():
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 270)
    cam.set(cv2.CAP_PROP_FPS, 30)

    _, frame = cam.read()
    cv2.imshow("Record Frame", frame)
    cv2.imshow("View Frame", frame)
    cv2.moveWindow("Record Frame", 0, 0)
    cv2.moveWindow("View Frame", 0, 393)

    barrier.wait()
    while True:
        _, frame = cam.read()
        cv2.imshow("Record Frame", frame)
        cv2.putText(frame, 'View', org=(50,50), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255,0,0))
        flip = cv2.flip(frame, 0)
        cv2.imshow("View Frame", flip)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
    cv2.destroyAllWindows()
    stop_event.set()
    cam.release()


def capture_audio():
    project = reapy.Project()
    barrier.wait()
    project.record()
    while not stop_event.is_set():
        pass
    project.stop()


rec_thread = threading.Thread(target=write_video)
cap_thread = threading.Thread(target=capture_video)
audio_rec_thread = threading.Thread(target=capture_audio)

barrier = threading.Barrier(3)

stop_event = threading.Event()

rec_thread.start()
cap_thread.start()
audio_rec_thread.start()
