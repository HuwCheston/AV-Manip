from threading import Event, Barrier
from CamThread import CamThread
from KeyThread import KeyThread
from ReaThread import ReaThread
from ReaEdit import edit_reaper_fx

# These variables can be edited
num_cameras = 1     # Number of cameras to try and read
params = {
    'flipped': False,   # V: rotates orthogonally A: no modification
    'delayed': False,   # V: adds five-second delay A: adds five-second delay (not yet implemented)
    'blanked': False,
    'looped': False,
    'pitch control': False,
    'volume control': False,
    '*delay time': 1000,  # The default amount of time to delay V/A by. Can be changed in GUI
    '*max delay time': 10000,  # The max amount of time (ms) to delay V/A by. Affects memory consumption!
    '*reset': False,
    '*quit': False,
    # Add more parameters as booleans here...
    # Params beginning with * are system parameters and will not be displayed in GUI
}

# These variables shouldn't be edited
STOPPER = Event()   # Used to interrupt main_loop for all objects (set by KeyThread)
BARRIER = Barrier((4 * num_cameras) + 1 + 1)  # ReaThread & KeyThread each use 1 thread, each CamThread uses 4 threads

if __name__ == "__main__":
    # Runs a checks to make sure Reaper JSFX params are equal to those defined above
    edit_reaper_fx(params)

    # Creates CamThread objects for the number of cameras specified by the user
    c = [CamThread(source=num, stop_event=STOPPER, global_barrier=BARRIER, params=params) for num in range(num_cameras)]

    # Creates single ReaThread and KeyThread objects
    r = ReaThread(stop_event=STOPPER, global_barrier=BARRIER, params=params)
    k = KeyThread(params=params, stop_event=STOPPER, global_barrier=BARRIER)
