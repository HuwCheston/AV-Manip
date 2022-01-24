import reapy
import time
import threading


class ReaThread:
    def __init__(self, stop_event: threading.Event, global_barrier: threading.Barrier, params: dict):
        # Initialisation
        self.project = reapy.Project()  # Initialise the Reaper project in Python
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

        # Main loop
        while not stop_event.is_set():  # stop_event is triggered by KeyThread
            # TODO: fix the logic here... this works for now, but won't when other FXs are added!
            if params['delayed'] and not keys.fxs[0].is_enabled:    # Don't try and enable if already enabled!
                keys.fxs[0].enable()

            elif not params['delayed']:
                for num in range(keys.n_fxs - 1):   # Don't want to disable final FX as it's the piano VST
                    keys.fxs[num].disable()    # Disable all FXs

            time.sleep(0.1)  # Improves performance in main_loop

        self.project.stop()     # Stops recording in Reaper
