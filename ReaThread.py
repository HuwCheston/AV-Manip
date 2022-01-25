import reapy
import time
import threading

# On certain machines (or a portable Reaper install), you may need to repeat the process of configuring Reapy every
# time you close and open Reaper. To do this, run the enable_distant_api.py script in Reaper (via Actions -> Show
# Action List -> Run Reascript), then call python -c "import reapy; reapy.configure_reaper()" in a terminal.


# TODO: refactor in the same manner as CamThread
class ReaThread:
    def __init__(self, stop_event: threading.Event, global_barrier: threading.Barrier, params: dict):
        # Initialisation
        self.project = reapy.Project()  # Initialise the Reaper project in Python
        for track in self.project.tracks:
            for num in range(track.n_fxs - 1):
                track.fxs[num].disable()
        reaper_thread = threading.Thread(target=self.main_loop, args=(stop_event, params))

        # Wait for other threads to complete initialisation
        print(f"Reaper manager currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

        # Main loop
        reaper_thread.start()

    def main_loop(self, stop_event, params):
        """
        Starts recording in Reaper, listens for keypresses from KeyThread to trigger manipulations.
        """
        self.project.record()   # Start recording in Reaper
        keys = self.project.tracks[0]

        # TODO: implement more FXs here...
        # Main loop
        while not stop_event.is_set():  # stop_event is triggered by KeyThread
            match params:
                case {'delayed': True} if not keys.fxs[0].is_enabled:
                    keys.fxs[0].enable()
                case {'reset': True}:
                    for num in range(keys.n_fxs - 1):   # Don't want to disable final FX as it's the piano VST
                        keys.fxs[num].disable()    # Disable all FXs
                    params['reset'] = False
            time.sleep(0.1)  # Improves performance in main_loop
        self.project.stop()     # Stops recording in Reaper
