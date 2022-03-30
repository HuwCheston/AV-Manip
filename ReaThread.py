import reapy
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
        self.track.name = track_name + ' - Delay'
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
        # self.vsti = self.track.add_fx(name=vst, input_fx=False, even_if_exists=False)


class ReaThread:
    def __init__(self, params: dict):
        # Initialise basic attributes
        self.project = reapy.Project()  # Initialise the Reaper project in Python
        self.params = params
        self.participants = [ReaTrack(project=self.project, track_name='Keys', track_index=0, vst='CollaB3 (Collab)',),
                             ReaTrack(project=self.project, track_name='Drums', track_index=1, vst='MT-PowerDrumKit',)]
        self.countin = self.project.tracks[self.project.n_tracks-1]

    def start_recording(self, bpm, auto_stop_bool=False, auto_stop_dur=0):
        # Sets the project BPM to value inputted by user (or to default provided in UserParams, if none provided in GUI)
        self.project.bpm = bpm if bpm is not None else self.params['*default bpm']
        # Sets the playback cursor to the position of the first marker, the start of the count-in
        self.project.cursor_position = self.project.markers[0].position
        # Start recording if not already
        if not self.project.is_recording:
            self.project.record()

    def stop_recording(self):
        # Stop if currently recording
        if self.project.is_recording:
            self.project.stop()
        # Sets the playback cursor to the position of the first marker, the start of the count-in
        self.project.cursor_position = self.project.markers[0].position

    def reset_manips(self):
        # Iterate through all the participants and turn off the FX used in manipulations (not the VSTi)
        for participant in self.participants:
            for fx in participant.manip_fx:
                fx.disable()
        self.project.unmute_all_tracks()

    def exit_loop(self):
        self.project.stop()
        self.reset_manips()

    def delayed_manip(self):
        for participant in self.participants:
            # Turn on the delay FX if it isn't turned on
            if not participant.delay_fx.is_enabled:
                participant.delay_fx.enable()
            # Set the delay time to equal the time set in the GUI
            participant.delay_fx.params[0] = self.params['*delay time']

    def pause_manip(self):
        self.project.mute_all_tracks()
