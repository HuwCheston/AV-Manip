import reapy
import time
import threading

# On certain machines (or a portable Reaper install), you may need to repeat the process of configuring Reapy every
# time you close and open Reaper. To do this, run the enable_distant_api.py script in Reaper (via Actions -> Show
# Action List -> Run Reascript), then call python -c "import reapy; reapy.configure_reaper()" in a terminal.

# TODO: I think the way this should be structured is as follows. A single ReaThread object is created, which manages
#  the project paramaters. This creates child classes equal to the number of participants. Each child has it's own
#  attributes relating to the participant + their partner's audio. The central ReaThread class runs the mainloop,
#  which triggers the modifications in the child classes.

class ReaThread:
    def __init__(self, global_barrier: threading.Barrier, stop_event: threading.Event, params: dict):
        self.project = reapy.Project()  # Initialise the Reaper project in Python
        self.params = params

        reaper_thread = threading.Thread(target=self.start_reaper, args=(global_barrier, stop_event))
        reaper_thread.start()

    def start_reaper(self, global_barrier, stop_event):
        self.reset_manips()
        self.wait(global_barrier)
        self.project.record()
        self.main_loop(stop_event)
        self.exit_loop()

    # TODO: i'm still not sure on the use of the staticmethod decorator here...
    @staticmethod
    def wait(global_barrier):
        print(f"Reaper manager currently waiting. Waiting threads = {global_barrier.n_waiting + 1}")
        global_barrier.wait()

    def main_loop(self, stop_event):
        keys = self.project.tracks[0]
        while not stop_event.is_set():  # stop_event is triggered by KeyThread
            # TODO: Does this need to be checked every loop iteration?
            keys.fxs[0].params[0] = self.params['*delay time']

            match self.params:
                case {'delayed': True} if not keys.fxs[0].is_enabled:
                    keys.fxs[0].enable()

                case {'pause audio': True} | {'pause both': True}:
                    self.project.mute_all_tracks()

                # case {'loop rec': True}:
                #     keys.fxs[2].enable()

                case {'*reset audio': True}:
                    self.reset_manips()

            time.sleep(0.1)  # Improves performance in main_loop

    def reset_manips(self):
        self.project.unmute_all_tracks()
        for track in self.project.tracks:
            for num in range(track.n_fxs - 1):
                track.fxs[num].disable()
        self.params['*reset audio'] = False

    def exit_loop(self):
        self.project.stop()
        self.reset_manips()
