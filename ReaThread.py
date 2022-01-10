import reapy
import time
import threading


class ReaThread:
    def __init__(self, stop_event: threading.Event, global_barrier: threading.Barrier, params: dict):
        self.project = reapy.Project()
        reaper_thread = threading.Thread(target=self.main_loop, args=(stop_event, params))

        print(f"Reaper manager currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()
        reaper_thread.start()

    def main_loop(self, stop_event, params):
        self.project.record()
        while not stop_event.is_set():
            time.sleep(0.1)
            if params['flipped']:
                print('flipped')    # Placeholder for when I get round to building keypress functionality into ReaThread
        self.project.stop()
