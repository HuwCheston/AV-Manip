from threading import Event, Barrier
from CamThread import CamThread
from KeyThread import KeyThread
from ReaThread import ReaThread
from ReaEdit import edit_reaper_fx
from UserParams import params

STOPPER = Event()   # Used to interrupt main_loop for all objects (set by KeyThread)
BARRIER = Barrier((4 * params['*participants']) + 1 + 1)  # ReaThread & KeyThread use 1 thread, each CamThread uses 4 threads

if __name__ == "__main__":
    # Runs a checks to make sure Reaper JSFX params are equal to those defined in UserParams
    edit_reaper_fx(params)

    # Creates CamThread objects for the number of cameras specified by the user
    c = [CamThread(source=num, stop_event=STOPPER, global_barrier=BARRIER, params=params)
         for num in range(params['*participants'])]

    # Creates single ReaThread and KeyThread objects
    r = ReaThread(stop_event=STOPPER, global_barrier=BARRIER, params=params)
    k = KeyThread(params=params, stop_event=STOPPER, global_barrier=BARRIER, reathread=r)
