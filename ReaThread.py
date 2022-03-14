import reapy
import threading
import time

# On certain machines (or a portable Reaper install), you may need to repeat the process of configuring Reapy every
# time you close and open Reaper. To do this, run the enable_distant_api.py script in Reaper (via Actions -> Show
# Action List -> Run Reascript), then call python -c "import reapy; reapy.configure_reaper()" in a terminal.

# TODO: I think the way this should be structured is as follows. A single ReaThread object is created, which manages
#  the project paramaters. This creates child classes equal to the number of participants. Each child has it's own
#  attributes relating to the participant + their partner's audio. The central ReaThread class runs the mainloop,
#  which triggers the modifications in the child classes.


class ReaTrack:
    def __init__(self, project: reapy.Project, track_name: str, track_index: int, vst: str):
        self.project = project
        self.track = self.project.tracks[track_index]
        self.track.name = track_name
        self.track.set_info_value('I_RECARM', 1)

        # If these FX don't exist, these lines will add them in. Otherwise, they will return the existing FX.
        self.delay_fx = self.track.add_fx(name='midi_delay', input_fx=False, even_if_exists=False)
        self.vst = self.track.add_fx(name=vst, input_fx=False, even_if_exists=False)


class ReaThread:
    def __init__(self, stop_event: threading.Event, params: dict):
        self.project = reapy.Project()  # Initialise the Reaper project in Python
        self.params = params
        self.name = 'Reaper Manager'
        self.stop_event = stop_event

        self.participants = [ReaTrack(project=self.project, track_name='Keys', track_index=0, vst='CollaB3 (Collab)',),
                             ReaTrack(project=self.project, track_name='Drums', track_index=1, vst='MT-PowerDrumKit',)]

        reaper_thread = threading.Thread(target=self.start_reaper,)
        reaper_thread.start()

    def start_reaper(self,):
        self.reset_manips()
        self.main_loop()
        self.exit_loop()

    def start_recording(self):
        if not self.project.is_recording:
            self.project.record()

    def stop_recording(self):
        if self.project.is_recording:
            self.project.stop()

    # TODO: implement reaper context manager here - should lead to performance increase!
    def main_loop(self,):
        while not self.stop_event.is_set():  # stop_event is triggered by KeyThread
            match self.params:

                case {'delayed': True}:
                    # Iterate through all the participants
                    for participant in self.participants:

                        # Turn on the delay FX if it isn't turned on
                        if not participant.delay_fx.is_enabled:
                            participant.delay_fx.enable()

                        # Set the delay time to equal the time set in the GUI
                        participant.delay_fx.params[0] = self.params['*delay time']

                case {'pause audio': True} | {'pause both': True}:
                    self.project.mute_all_tracks()

                case {'*reset audio': True}:
                    self.reset_manips()
            time.sleep(0.1)

    def reset_manips(self):
        self.project.unmute_all_tracks()
        for track in self.project.tracks:
            for num in range(track.n_fxs - 1):
                track.fxs[num].disable()
        self.params['*reset audio'] = False

    def exit_loop(self):
        self.project.stop()
        self.reset_manips()
