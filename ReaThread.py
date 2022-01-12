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

        # Main loop
        while not stop_event.is_set():  # stop_event is trigerred by KeyThread
            time.sleep(0.1)     # Improves performance in main_loop
            if params['flipped']:   # Placeholder for triggering modifications in Reaper when set by KeyThread
                pass

        self.project.stop()     # Stops recording in Reaper
