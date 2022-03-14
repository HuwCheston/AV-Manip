import threading
import time
import tkinter
from tkinter import Button
from TkGui import TkGui


class KeyThread:
    def __init__(self, params: dict, stop_event: threading.Event, global_barrier: threading.Barrier, reathread):
        self.name = 'Keypress Manager'
        self.stop_event = stop_event
        self.params = params
        self.gui = TkGui(params=self.params, keythread=self)
        self.reathread = reathread
        self.start_keymanager(global_barrier)

    def start_keymanager(self, global_barrier):
        self.wait(global_barrier)
        self.gui.tk_setup()
        self.main_loop()

    def wait(self, global_barrier):
        print(f"{self.name} currently waiting. Waiting threads = {global_barrier.n_waiting + 1}\n")
        global_barrier.wait()

    def main_loop(self):
        self.gui.root.mainloop()

    def exit_loop(self):
        self.reset_manips()
        # TODO: fix this so that sleeping time is logged
        for num in range(self.params['*exit time'], 0, -1):
            # Wait to make sure everything has shut down (prevents tkinter RunTime errors w/threading)
            time.sleep(1)
            # self.gui.log_text('asdf')
            # self.gui.root.after(num*1000, func=self.gui.log_text(f'\nExiting in {num}...'))
        self.stop_event.set()
        self.gui.root.destroy()

    def enable_manip(self, manip, button):
        self.reset_manips()
        self.params[manip] = True
        button.config(bg='green')
        self.gui.log_text(text=f'\n{manip} now active.')

    def reset_manips(self):
        self.gui.log_text(text='\nResetting...')
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
