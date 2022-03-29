import tkinter as tk
from DelayPanes import VariableDelay, IncrementalDelay, FixedDelay, DelayFromFile, get_tk_entry, try_get_entry
from GuiPanes import *


class TkGui:
    def __init__(self, params, keythread):
        self.root = tk.Tk()
        self.root.title('AV-Manip')
        self.root.attributes('-topmost', 'true')
        self.root.iconbitmap("cms-logo.ico")

        self.file_delay = None
        self.logging_window = None

        self.params = params
        self.keythread = keythread
        self.tk_list = []
        self.buttons_list = []

        self.manip_panes = {
            'Fixed Delay': FixedDelay,
            'Delay from File': DelayFromFile,
            'Variable Delay': VariableDelay,
            'Incremental Delay': IncrementalDelay,
            'Loop Audio/Video': LoopPane,
            'Pause Audio/Video': PausePane,
            'Blank Video': BlankPane,
            'Control Audio': ControlPane,
            'Flip Video': FlipPane
        }
        self.kwargs = {
            "root": self.root,
            "keythread": self.keythread,
            "params": self.params,
            "gui": self
        }

    def tk_setup(self):
        info_pane = InfoPane(root=self.root, keythread=self.keythread, params=self.params, gui=self)
        self.logging_window = info_pane.logging_window
        info_pane.tk_frame.grid(column=0, row=1, sticky='n', padx=10, pady=10)
        for (num, pane) in enumerate([CommandPane, PresetPane, ManipChoicePane]):
            p = pane(root=self.root, keythread=self.keythread, params=self.params, gui=self)
            p.tk_frame.grid(column=num+1, row=1, sticky='n', padx=10, pady=10)

    def add_manip_to_frame(self, pane):
        self.keythread.reset_manips()
        for frame in self.root.grid_slaves():
            if int(frame.grid_info()["column"]) > 4:
                frame.grid_forget()
        new_pane = pane(root=self.root, keythread=self.keythread, params=self.params, gui=self)
        new_pane.tk_frame.grid(column=5, row=1, sticky='n', padx=10, pady=10)
        self.buttons_list = [widget for widget in new_pane.tk_list if isinstance(widget, tk.Button)]

    def log_text(self, text):
        self.logging_window.config(state='normal')
        self.logging_window.insert('end', '\n' + text)
        self.logging_window.see("end")
        self.logging_window.config(state='disabled')
