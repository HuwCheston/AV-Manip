import threading
from CamThread import CamThread
from KeyThread import KeyThread
from ReaThread import ReaThread

PARAMS = {
    'flipped': False,
    'delayed': False,
}
STOPPER = threading.Event()
BARRIER = threading.Barrier(9)

if __name__ == "__main__":
    camera1 = CamThread(source=0, stop_event=STOPPER, global_barrier=BARRIER, params=PARAMS)
    camera2 = CamThread(source=1, stop_event=STOPPER, global_barrier=BARRIER, params=PARAMS)
    reaper = ReaThread(stop_event=STOPPER, global_barrier=BARRIER, params=PARAMS)
    keylogger = KeyThread(params=PARAMS, stop_event=STOPPER, )
