from threading import Event, Barrier
from CamThread import CamThread
from KeyThread import KeyThread
from ReaThread import ReaThread

# These variables can be edited
num_cameras = 1     # Number of cameras to try and read
params = {
    'flipped': False,   # V: rotates orthogonally A: no modification
    'delayed': False,   # V: adds five-second delay A: adds five-second delay (not yet implemented)
    # Add more parameters as booleans here...
}

# These variables shouldn't be edited
STOPPER = Event()   # Used to interrupt main_loop for all objects (set by KeyThread)
BARRIER = Barrier((4 * num_cameras) + 1)  # ReaThread uses 1 thread, each CamThread uses 4 threads

if __name__ == "__main__":
    # Creates CamThread objects for the number of cameras specified by the user
    c = [CamThread(source=num, stop_event=STOPPER, global_barrier=BARRIER, params=params) for num in range(num_cameras)]

    # TODO: remove this (and any other) redundant comments
    r = ReaThread(stop_event=STOPPER, global_barrier=BARRIER, params=params)
    k = KeyThread(params=params, stop_event=STOPPER)
