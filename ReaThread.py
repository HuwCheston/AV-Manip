import reapy
from reapy import reascript_api as RPR
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
        # Set the track name and arm it for recording
        self.track = project.tracks[track_index]
        self.track.name = track_name
        self.track.set_info_value('I_RECARM', 1)

        # If any of these FX don't exist, these lines will add them in.
        # These FX are used to trigger manipulations.
        self.delay_fx = self.track.add_fx(name='midi_delay', input_fx=False, even_if_exists=False)
        self.manip_fx = [
            self.delay_fx,
            # More FX should be added here as and when they are required.
            # Adding FXs into this list makes it easy to turn them all off when reset_manips() is called.
        ]

        # This FX should not normally be touched, as it's used to convert the MIDI into audio
        self.vsti = self.track.add_fx(name=vst, input_fx=False, even_if_exists=False)


class ReaThread:
    def __init__(self, stop_event: threading.Event, params: dict):
        # Initialise basic attributes
        self.project = reapy.Project()  # Initialise the Reaper project in Python
        self.params = params
        self.stop_event = stop_event

        self.participants = [ReaTrack(project=self.project, track_name='Keys', track_index=0, vst='CollaB3 (Collab)',),
                             ReaTrack(project=self.project, track_name='Drums', track_index=1, vst='MT-PowerDrumKit',)]
        self.countin = self.project.tracks[self.project.n_tracks-1]

        # reaper_thread = threading.Thread(target=self.start_reaper,)
        # reaper_thread.start()

    def start_reaper(self,):
        self.reset_manips()
        self.main_loop()
        self.exit_loop()

    def start_recording(self, bpm):
        # Including this for safety
        self.reset_manips()

        # Sets the project BPM to value inputted by user (or to default provided in UserParams, if none provided in GUI)
        self.project.bpm = bpm if bpm is not None else self.params['*default bpm']

        # Sets the playback cursor to the position of the first marker, the start of the count-in
        self.project.cursor_position = self.project.markers[0].position

        # Start recording if not already
        if not self.project.is_recording:
            self.project.record()

        # while True:
        #     if self.project.play_position < self.project.markers[1].position:
        #         print('before countin')
        #     else:
        #         print('after countin')

    def stop_recording(self):
        # Including this for safety
        self.reset_manips()

        # Stop if currently recording
        if self.project.is_recording:
            self.project.stop()

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
        # This is here in case the 'pause audio/both' manipulation has been used
        self.project.unmute_all_tracks()

        # Iterate through all the participants and turn off the FX used in manipulations (not the VSTi)
        for participant in self.participants:
            for fx in participant.manip_fx:
                fx.disable()

        self.params['*reset audio'] = False

    def exit_loop(self):
        self.project.stop()
        self.reset_manips()

    def set_delay(self):
        for participant in self.participants:
            # Turn on the delay FX if it isn't turned on
            if not participant.delay_fx.is_enabled:
                participant.delay_fx.enable()
            # Set the delay time to equal the time set in the GUI
            participant.delay_fx.params[0] = self.params['*delay time']
