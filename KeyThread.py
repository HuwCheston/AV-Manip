import threading
from tkinter import Button
from TkGui import TkGui


class KeyThread:
    def __init__(self, params: dict, stop_event: threading.Event, global_barrier: threading.Barrier):
        self.name = 'Keypress Manager'
        self.stop_event = stop_event
        self.params = params
        self.gui = TkGui(params=self.params, keythread=self)
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
        self.stop_event.set()
        self.gui.root.destroy()

    def enable_manip(self, manip, button):
        self.reset_manips()
        self.params[manip] = True
        button.config(bg='green')

    def set_delay_time(self, d_time):
        try:
            d = int(d_time.get())
        except ValueError:
            d_time.delete(0, 'end')
            d_time.insert(0, 'Not a number')
        else:
            if 0 < d < self.params['*max delay time']:
                self.params['*delay time'] = d
            else:
                d_time.delete(0, 'end')
                d_time.insert(0, 'Out of bounds')

    def reset_manips(self):
        self.params['*reset video'] = True  # This param is reset to False by CamThread once resetting has completed
        self.params['*reset audio'] = True  # This param is reset to False by ReaThread once resetting has completed

        for b in self.gui.tk_list:
            if isinstance(b, Button):
                b.config(bg="SystemButtonFace")
        for param in self.params.keys():
            if isinstance(self.params[param], bool) and not param.startswith('*'):
                self.params[param] = False
