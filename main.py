from threading import Event, Barrier
from CamThread import CamThread
from KeyThread import KeyThread
from ReaThread import ReaThread

# These variables can be edited to account for differing numbers of cameras or desired modification parameters
num_cameras = 2
params = {
    'flipped': False,
    'delayed': False,
    # More can be added here and will be passed to all the appropriate threads (functionality needs to be built though)
}

# These variables shouldn't be edited
STOPPER = Event()
BARRIER = Barrier((4 * num_cameras) + 1)  # ReaThread uses 1 thread, each CamThread uses 4 threads

if __name__ == "__main__":
    cam_list = []
    for num in range(num_cameras):
        cam_list.append(CamThread(source=num, stop_event=STOPPER, global_barrier=BARRIER, params=params))
    reaper = ReaThread(stop_event=STOPPER, global_barrier=BARRIER, params=params)
    keylogger = KeyThread(params=params, stop_event=STOPPER)
