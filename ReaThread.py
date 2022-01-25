import reapy
import time
import threading

# On certain machines (or a portable Reaper install), you may need to repeat the process of configuring Reapy every
# time you close and open Reaper. To do this, run the enable_distant_api.py script in Reaper (via Actions -> Show
# Action List -> Run Reascript), then call python -c "import reapy; reapy.configure_reaper()" in a terminal.


class ReaThread:
    def __init__(self, global_barrier: threading.Barrier, stop_event: threading.Event, params: dict):
        self.project = reapy.Project()  # Initialise the Reaper project in Python
        reaper_thread = threading.Thread(target=self.start_reaper, args=(global_barrier, stop_event, params))
        reaper_thread.start()

    def start_reaper(self, global_barrier, stop_event, params):
        self.disable_fxs()
        self.wait(global_barrier)
        self.project.record()
        self.main_loop(stop_event, params)
        self.exit_loop()

    def disable_fxs(self):
        for track in self.project.tracks:
            for num in range(track.n_fxs - 1):
                track.fxs[num].disable()

    @staticmethod
    def wait(global_barrier):
        print(f"Reaper manager currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

    def main_loop(self, stop_event, params):
        keys = self.project.tracks[0]
        while not stop_event.is_set():  # stop_event is triggered by KeyThread
            match params:
                case {'delayed': True} if not keys.fxs[0].is_enabled:
                    keys.fxs[0].enable()
                case {'reset': True}:
                    self.disable_fxs()
                    params['reset'] = False
            time.sleep(0.1)  # Improves performance in main_loop

    def exit_loop(self):
        self.project.stop()
        self.disable_fxs()
