from DelayPanes import VariableDelay, IncrementalDelay, FixedDelay, DelayFromFile
from GuiPanes import *


class TkGui:
    def __init__(self, params, keythread):
        self.root = tk.Tk()
        self.root.title('AV-Manip')
        self.root.attributes('-topmost', 'true')
        self.root.iconbitmap("cms-logo.ico")
        self.params = params
        self.keythread = keythread

        self.file_delay = None
        self.logging_window = None

        # These are the manip panes we have available. Whenever a new choice is selected in the ManipChoicePane
        # combobox, the relevent class will be selected from the list and its frame packed into the GUI.
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
        # Whenever we create a new pane class, this dictionary will be passed in as its kwargs
        self.kwargs = {
            "root": self.root,
            "keythread": self.keythread,
            "params": self.params,
            "gui": self
        }
        # Whenever a new pane is created, we should add its buttons into here so that we can reset their appearance
        # later in keythread.
        self.buttons_list = []

    def tk_setup(self):
        # TODO: tidy this up (into separate classes?)
        info_pane = InfoPane(**self.kwargs)
        self.logging_window = info_pane.logging_window
        info_pane.tk_frame.grid(column=0, row=1, sticky='n', padx=10, pady=10)

        # TODO: if this is pane = pane(**self.kwargs), does that mean that we can include InfoPane in the list? might update the reference
        for (num, pane) in enumerate([CommandPane, PresetPane, ManipChoicePane]):
            p = pane(**self.kwargs)
            p.tk_frame.grid(column=num+1, row=1, sticky='n', padx=10, pady=10)

    def add_manip_to_frame(self, pane):
        # We need to reset all our manipulations first so we don't run into any issues
        self.keythread.reset_manips()
        # Iterate through all the frames packed into our gui root
        for frame in self.root.grid_slaves():
            # If a frame is a manip, it will be packed after the command panes, so we can safely forget it
            if int(frame.grid_info()["column"]) > 4:
                frame.grid_forget()
        # TODO: creating a new pane should be a separate function
        new_pane = pane(**self.kwargs)
        # TODO: the column number shouldn't be magic (use length of a default panes list or something)
        new_pane.tk_frame.grid(column=5, row=1, sticky='n', padx=10, pady=10)
        self.buttons_list = [widget for widget in new_pane.tk_list if isinstance(widget, tk.Button)]

    def log_text(self, text):
        self.logging_window.config(state='normal')
        self.logging_window.insert('end', '\n' + text)
        self.logging_window.see("end")
        self.logging_window.config(state='disabled')
