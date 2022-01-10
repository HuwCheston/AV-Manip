import reapy
import time
import threading


class ReaThread:
    def __init__(self, stop_event, global_barrier):
        self.project = reapy.Project()
        self.reaper_thread = threading.Thread(target=self.main_loop, args=(stop_event,))
        print(f"Reaper manager currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()
        self.reaper_thread.start()

    def main_loop(self, stop_event):
        self.project.record()
        while not stop_event.is_set():
            time.sleep(0.1)
        self.project.stop()