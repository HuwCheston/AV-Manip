from DelayPanes import VariableDelay, IncrementalDelay, FixedDelay, DelayFromFile
from GuiPanes import *


class TkGui:
    def __init__(self, params, keythread):
        self.root = tk.Tk()
        self.set_root_appearance()
        self.params = params
        self.keythread = keythread
        self.logging_window = None  # This attribute will be set later when we pack our default_panes

        # These are the panes that should be active at all times, and are packed at startup
        self.info_pane, self.command_pane, self.preset_pane, self.manip_choice_pane = InfoPane, CommandPane, PresetPane, ManipChoicePane
        self.default_panes = [
            self.info_pane,
            self.command_pane,
            self.preset_pane,
            self.manip_choice_pane,
        ]
        # These are the manip panes we have available. Whenever a new choice is selected in the ManipChoicePane
        # combobox, the relevent class will be selected from the list and its frame packed into the GUI.
        self.manip_panes = {
            'Fixed Delay': FixedDelay,
            'Delay From File': DelayFromFile,
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
        # later in the reset_manips function in keythread.
        self.buttons_list = []

    def set_root_appearance(self):
        self.root.title('AV-Manip')
        self.root.attributes('-topmost', 'true')
        self.root.iconbitmap("cms-logo.ico")

    def tk_setup(self):
        # Iterate through our list of default panes
        for (num, pane) in enumerate(self.default_panes):
            p = self.create_and_pack_frame(pane=pane, num=num)
            # Set the logging window attribute to the InfoPane logging window (use try-except to adhere with EAFP)
            try:
                self.logging_window = p.logging_window
            except AttributeError:
                pass

    def create_and_pack_frame(self, pane, num):
        # Initialise our new pane with the required kwargs dictionary
        new_pane = pane(**self.kwargs)
        # Pack each pane into the gui root with the required column
        new_pane.tk_frame.grid(column=num, row=1, sticky='n', padx=10, pady=10)
        # We can return our new pane as we might need it later
        return new_pane

    def unpack_existing_manip_frame(self):
        # Iterate through all the frames packed into our gui root
        for frame in self.root.grid_slaves():
            # If a frame is a manip, it will be packed after the command panes, so we can safely forget it
            if int(frame.grid_info()["column"]) > len(self.default_panes):
                frame.grid_forget()

    def add_manip_to_root(self, pane):
        # We need to reset all our manipulations first so we don't run into any issues
        self.keythread.reset_manips()
        # Unpack our existing manip frames
        self.unpack_existing_manip_frame()
        # Pack the new pane into the GUI, in the next column after the default_panes
        col_num = len(self.default_panes) + 1
        new_pane = self.create_and_pack_frame(pane=pane, num=col_num)
        # Change this attribute so we can reset the appearance of our buttons later in keythread when resetting
        self.buttons_list = [widget for widget in new_pane.tk_list if isinstance(widget, tk.Button)]
        return new_pane

    def log_text(self, text):
        self.logging_window.config(state='normal')
        self.logging_window.insert('end', '\n' + text)
        self.logging_window.see("end")
        self.logging_window.config(state='disabled')

    def preset_handler(self, preset: dict):
        manip_pane = self.manip_panes[preset['Manipulation']]
        preset_pane = self.add_manip_to_root(pane=manip_pane)
        if preset['Manipulation'] == 'Delay From File':
            insert_into_entry(preset_pane.resample_entry, preset['Resample Rate'])
            if preset['Scale Delay']:
                preset_pane.checkbutton_var.set(1)
                insert_into_entry(preset_pane.baseline_entry, preset['Baseline'])
                preset_pane.multiplier.set(preset['Multiplier'])
            # We want to set our file parameter last, so we can use the above parameters to scale it successfully
            preset_pane.file_to_array(filename=preset['File'])
        elif preset['Manipulation'] == 'Fixed Delay':
            insert_into_entry(preset_pane.delay_time_entry, preset['Delay Time'])
        # TODO: add code in here to account for other types of preset manipulation...


def insert_into_entry(entry, text):
    entry.config(state='normal')
    entry.delete(0, 'end')
    entry.insert('end', text)
