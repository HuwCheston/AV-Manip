import timeit
import time
from cv2 import cv2


width = 640
height = 480
fps = 30
camera_channel = 1
fname = "camera_latency"
wait_time = 1

cv2.namedWindow("preview")
cam = cv2.VideoCapture(camera_channel)
cam.set(cv2.CAP_PROP_FPS, fps)

################################################
time.sleep(2)
font = cv2.FONT_HERSHEY_SIMPLEX
returned_deltas = []
frame = None

try:
    if cam.isOpened():  # try to get the first frame
        rval, frame = cam.read()
    else:
        rval = False
    ii = 100
    time_end = time.time() + 30
    toc = 0
    tic = timeit.default_timer()
    while time.time() < time_end:
        toc_old = toc
        toc = timeit.default_timer()
        delta = toc - toc_old
        returned_deltas.append(delta)
        print("delta: %0.3f  fps: %0.3f" % (delta, 1/delta))

        cv2.putText(frame, "%0.3f" % (toc - tic), (50, 200), font, 2, (255, 255, 255), 4, cv2.LINE_AA)
        cv2.imshow("preview", frame)
        key = cv2.waitKey(wait_time)

        # Monitor keyboard
        if key == 27:  # exit on ESC
            break
        elif key == 32:
            cv2.imwrite(fname + str(ii) + ".jpg", frame)
            ii += 1
        rval, frame = cam.read()

finally:
    cam.release()
    cv2.destroyAllWindows()
    del returned_deltas[0]  # Not sure why the first element is always really long, but delete it anyway!
    average_delta = sum(returned_deltas)/len(returned_deltas)
    print(f'Average lag = {average_delta} seconds or {average_delta*1000} milliseconds')
