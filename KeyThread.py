import threading
import time
import datetime
import tkinter
from TkGui import TkGui


class KeyThread:
    def __init__(self,
                 params: dict,
                 stop_event: threading.Event,
                 reathread,
                 camthread: list):
        self.name = 'Keypress Manager'
        self.stop_event = stop_event
        self.params = params
        self.gui = TkGui(params=self.params, keythread=self)
        self.reathread = reathread
        self.camthread = camthread
        self.start_keymanager()

    def start_keymanager(self):
        self.gui.tk_setup()
        self.main_loop()

    def main_loop(self):
        self.gui.root.mainloop()

    def exit_loop(self):
        self.reset_manips()
        for num in range(self.params['*exit time'], 0, -1):
            # Wait to make sure everything has shut down (prevents tkinter RunTime errors w/threading)
            time.sleep(1)
        self.stop_recording()
        self.stop_event.set()
        self.gui.root.destroy()

    def enable_manip(self, manip, button):
        self.reset_manips()
        self.params[manip] = True
        button.config(bg='green')
        self.gui.log_text(text=f'{manip} now active.')

    def reset_manips(self):
        self.gui.log_text(text='Resetting...')
        self.params['*reset video'] = True  # This param is reset to False by CamThread once resetting has completed
        for param in self.params.keys():
            if isinstance(self.params[param], bool) and not param.startswith('*'):
                self.params[param] = False
        for b in self.gui.buttons_list:
            try:
                b.config(bg="SystemButtonFace")
            except tkinter.TclError:
                pass

        # Allows time for all threads relying on params being true to finish. This helps avoid the reaper socket closing
        # unexpectedly if it tries to execute two commands simultaneously (e.g. setting delay time, turning off fx)
        time.sleep(1)
        self.reathread.reset_manips()
        self.gui.log_text(text='done!')

    def start_recording(self, bpm):
        # We need to reset all of our manips before starting the recording (can turn them on after)
        self.reset_manips()
        # Start the recording in both reathread and for all of our camthreads
        self.reathread.start_recording(bpm)
        _ = [threading.Thread(target=cam.cam_write.start_recording).start() for cam in self.camthread]
        self.params['*recording'] = True    # This parameter is used to add text onto the camera view
        self.gui.log_text(text=f'Started recording at {datetime.datetime.now().strftime("%H:%M:%S")}')

    def stop_recording(self):
        # We need to reset all of our manips before stopping the recording (can turn them on after)
        self.reset_manips()
        # Stop the recording in both reathread and for all our camthreads
        self.reathread.stop_recording()
        for cam in self.camthread:
            cam.cam_write.stop_recording()
        self.params['*recording'] = False    # This parameter is used to remove text from the camera view
        self.gui.log_text(text=f'Finished recording at {datetime.datetime.now().strftime("%H:%M:%S")}')
