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
        self.params['*reset audio'] = True  # This param is reset to False by ReaThread once resetting has completed

        for b in self.gui.buttons_list:
            try:
                b.config(bg="SystemButtonFace")
            except tkinter.TclError:
                pass

        for param in self.params.keys():
            if isinstance(self.params[param], bool) and not param.startswith('*'):
                self.params[param] = False

        # TODO: check this doesn't break anything (should probably also be np.zeros)
        # self.gui.file_delay.file = None     # Clear out any saved array

        self.gui.log_text(text='done!')

    def start_recording(self):
        self.reathread.start_recording()
        _ = [threading.Thread(target=cam.cam_write.start_recording).start() for cam in self.camthread]
        self.gui.log_text(text=f'Started recording at {datetime.datetime.now().strftime("%H:%M:%S")}')

    def stop_recording(self):
        self.reathread.stop_recording()
        for cam in self.camthread:
            cam.cam_write.stop_recording()
        self.gui.log_text(text=f'Finished recording at {datetime.datetime.now().strftime("%H:%M:%S")}')
