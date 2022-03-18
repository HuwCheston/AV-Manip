import tkinter as tk
from tkinter import ttk, filedialog
import json
import os


manip_names = {
    'Delay From File': {
        'File': 'file',
        'Resample Rate': 'int',
        'Scale Delay': 'bool',
        'Baseline': 'int',
        'Multiplier': 'float'
    },
    'Fixed Delay': {
        'Delay Time': 'int'
    },
    'Variable Delay': {
        'Distributions': [
                'Uniform',
                'Gaussian',
                'Poisson',
        ],
    },
    'Incremental Delay': {
        'Distributions': [
            'Linear',
            'Exponential',
            'Natural Log'
        ],
        'Starting Value': 'int',
        'Finishing Value': 'int',
        'Resample Rate': 'int',
    },
}


def keep_focus(func):
    def _decorator(self, *args, **kwargs):
        self.creator_window.attributes('-topmost', 0)
        func(self, *args, **kwargs)
        self.creator_window.attributes('-topmost', 1)
    return _decorator


class PresetPane:
    def __init__(self, root: tk.Tk):
        """This class creates a pane in TkGui that enables the user to load and create manipulation presets"""
        # Initialise basic parameters
        self.root = root
        self.presets_dir = './input/'
        self.presets_list = []
        # All widgets should go into this tk_pane, which should be accessed in TkGui and packed
        self.tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        # Initialise the preset selector combobox with default functionality (i.e. no presets loaded)
        self.presets_combo = ttk.Combobox(self.tk_frame, state='readonly',)
        self.reset_preset_combo()
        # These widgets should be packed in TkGui
        self.tk_list = [
            tk.Label(self.tk_frame, text='Presets'),
            tk.Button(self.tk_frame, text="Open Preset Creator", command=self.open_preset_creator),
            tk.Button(self.tk_frame, text="Load Preset Folder", command=self.open_preset_folder),
            self.presets_combo
        ]

    def open_preset_folder(self):
        """Prompts for the user to select a directory to search for valid preset files in"""
        # Open the directory
        f = tk.filedialog.askdirectory(title='Open presets folder', initialdir=self.presets_dir,)
        # Tk askdirectory returns None if dialog closed with cancel
        if f == '':
            return
        # If a valid directory has been selected, try and get jsons from it
        else:
            self.presets_dir = f
            self.get_jsons_from_dir()

    def get_jsons_from_dir(self):
        """Searches through a directory for preset files and adds them to a list if they're valid"""
        # Reset the combobox to neutral
        self.reset_preset_combo()
        # Get all the json files in our directory
        jsons = [f for f in os.listdir(self.presets_dir) if f.endswith('.json')]
        # Iterate through our json files and add those that are valid to our preset list
        for js in jsons:
            f = json.loads(open(self.presets_dir + '/' + js, 'r').read())
            if self.check_json(js=f):
                self.presets_list.append(f)
        # We only want to update the functionality of our combobox if valid presets have been loaded
        if len(self.presets_list) > 0:
            self.populate_preset_combo()

    @staticmethod
    def check_json(js: dict):
        """Checks if a particular json file contains valid information for the application"""
        # This key should always be present in any valid .JSON made for use with this software
        if 'Manipulation' not in js:
            return False
        # TODO: check that this works in cases where a checkbutton is used
        # If the user entered nothing in a field, discard the JSON
        elif any(v == '' for v in js.values()):
            return False
        # If the json passes the above checks, it is valid
        else:
            return True

    def populate_preset_combo(self):
        """Populates the preset combobox with valid preset files"""
        # Format the string to display in the combobox, including the manipulation name & preset number
        presets = [f'Preset {num + 1}: {k["Manipulation"]}' for (num, k) in enumerate(self.presets_list)]
        # Update the combobox values and default text
        self.presets_combo.config(values=presets)
        self.presets_combo.set('Select Preset')
        # Enable the combobox functionality
        self.presets_combo.bind("<<ComboboxSelected>>", lambda x: self.preset_combo_func())

    def preset_combo_func(self):
        """Sends the preset selected in the combobox to TkGui"""
        # Look through the list of combobox values, and get the index of the one selected.
        combo_ind = self.presets_combo['values'].index(self.presets_combo.get())
        # The combobox doesn't display the full preset, so get this from the JSON list using the index
        selected_preset = self.presets_list[combo_ind]
        # Send this information to TkGui to create the correct pane and fill in the values
        print(selected_preset)

    def reset_preset_combo(self):
        """Resets the functionality and appearance of the preset combobox"""
        # Clear out any previously saved presets from the list
        self.presets_list.clear()
        # Reset the functionality of the combobox, the values displayed within it, and the default text
        self.presets_combo.bind("<<ComboboxSelected>>", '')
        self.presets_combo.configure(values=[])
        self.presets_combo.set('No Presets Loaded!')

    def open_preset_creator(self):
        """Creates a new toplevel window to allow the user to create preset files"""
        pc = PresetCreator(root=self.root)
        pc.create_window()


class PresetCreator:
    def __init__(self, root: tk.Tk):
        """A class that enables the user to create .JSON files that can be loaded to preset manipulation parameters."""
        # Initialise basic class parameters
        self.root = root
        self.manip_list = manip_names
        self.filename = ''
        self.default_path = './input/'

        # Initialise these as None so they can be altered later
        self.creator_window = None
        self.creator_frame = None
        self.manip_options = None

    def create_window(self):
        """Initialise a new preset creator window"""
        # Destroy any existing toplevel windows
        self.clear_out_windows()

        # Initialise new top level window with required attributes
        self.creator_window = tk.Toplevel(self.root)
        self.creator_window.title('Preset Creator')
        self.creator_window.geometry("%dx%d%+d%+d" % (300, 300, 250, 125))
        self.creator_window.attributes('-topmost', 'true')
        self.creator_window.iconbitmap("cms-logo.ico")

        # Widgets created here will not be cleared whenever a new manipulation is selected - e.g. combobox
        self.creator_frame = tk.Frame(self.creator_window, borderwidth=2, relief="groove")
        _ = tk.Label(self.creator_frame, text='Preset Creator').pack()
        _ = tk.Label(self.creator_frame,
                     text='Use this tool to create preset .JSON files').pack()
        self.creator_frame.pack(padx=10, pady=10, anchor='center')

        # Widgets created here will be cleared whenever a new manipulation is selected - these are the parameters
        self.manip_options = tk.Frame(self.creator_frame)
        self.choose_manip()

    def choose_manip(self):
        """Display a combobox to allow the user to choose a manipulation"""
        # Fill the combobox options with the possible manipulations
        combo = ttk.Combobox(self.creator_frame, state='readonly',
                             values=[k for k in self.manip_list.keys()])
        combo.set('Choose a Manipulation')
        # Create the necessary labels/entries whenever a new manipulation is selected
        combo.bind("<<ComboboxSelected>>", lambda e: self.manip_selected(combo.get()))
        combo.pack(padx=1, pady=1, anchor='center')

    def manip_selected(self, manip):
        """Display the parameters of the selected manipulation for the user to enter info"""
        self.clear_out_widgets()
        d = self.manip_list[manip]
        # Create frames (according to number of parameters)
        frames = [tk.Frame(self.manip_options) for _ in d.items()]
        # Create labels (according to keys)
        labels = self.preset_labels(d, frames)
        # Create entries (according to values)
        entries = self.preset_entries(d, frames)
        for frame in frames:
            frame.pack(anchor='center')
        # Create submission button
        submit = tk.Button(self.manip_options,
                           command=lambda: self.submit_preset(labels, entries, manip),
                           text='Save Preset as .JSON')
        submit.pack(padx=1, pady=1, anchor='center')

    @staticmethod
    def preset_labels(d: dict, frames: list) -> list:
        """Add the correct text labels for the parameters of the selected manipulation"""
        labels = []
        for num, lab in enumerate(d.keys()):
            w = tk.Label(frames[num], text=lab + ': ')
            labels.append(w)
            w.grid(column=1, row=1, sticky="n", padx=1, pady=1)
        return labels

    def preset_entries(self, d: dict, frames: list) -> list:
        """Add the correct entry widgets for the parameters of the selected manipulation"""
        entries = []
        for num, ty in enumerate(d.values()):
            # If the parameter is a boolean, create a checkbutton
            if ty == 'bool':
                var = tk.IntVar()
                w = tk.Checkbutton(frames[num], variable=var)
                # This command allows us to get the value later without using our IntVar
                w.val = var
            # If the parameter is an int, create an entry frame that can only have numbers inserted into it
            elif ty == 'file':
                file_open = tk.Button(frames[num], text='Open File')
                file_open.config(command=lambda: self.open_file(file_open)),
                w = file_open
            elif ty == 'int':
                w = tk.Entry(frames[num], validate="key", width=5)
                # This command prevents us from inserting anything other than numbers
                w['validatecommand'] = (w.register(self.validate_int), '%P', '%d')
                # Create a label after the entry indicating the unit
                _ = tk.Label(frames[num], text='ms').grid(row=1, column=3, sticky="n", padx=1, pady=1)
            # If the parameter is a float, create a slider
            elif ty == 'float':
                var = tk.DoubleVar()
                w = tk.Scale(frames[num], from_=0, to=3.0, resolution=0.1, orient='horizontal', variable=var)
                # This command allows us to get the value later without using our DoubleVar
                w.val = var
            # If the parameter is a list, create a combobox and populate it with the values from our list
            elif isinstance(ty, list):
                w = ttk.Combobox(frames[num], state='readonly', values=[k for k in ty], width=12)
            # If the parameter is a string, create an entry window with no restrictions on input
            else:
                w = tk.Entry(frames[num], width=5)
                w.insert('end', 'String')
            # Pack the entry window and append to the list
            w.grid(column=2, row=1, sticky="n", padx=1, pady=1)
            entries.append(w)
        return entries

    @keep_focus
    def open_file(self, button):
        """Open a file and store its location."""
        filetypes = (
            ('CSV files', '*.csv'),
            ('Text files', '*.txt'),
        )
        # Open the file
        f = tk.filedialog.askopenfile(title='Open a file', initialdir='./input/', filetypes=filetypes)

        # Tk askopenfile returns None if dialog closed with cancel
        if f is None:
            return
        # Only allow the user to open accepted filetypes
        elif f.name.endswith(tuple(ty[1].strip('*') for ty in filetypes)):
            button.config(bg='green', text='File loaded')
            self.filename = f.name
        # Block the user from opening files of invalid type
        else:
            button.config(bg='red', text='Invalid file')

    @staticmethod
    def validate_int(s, acttyp) -> bool:
        """Used to ensure the user can only enter numbers into tk.Entry windows where integers are required"""
        if acttyp == '1':  # insert
            if not s.isdigit():
                return False
        return True

    @keep_focus
    def submit_preset(self, labels: list, entries: list, manip: str):
        """Creates .JSON file with parameters entered by user, prompts for a location to save, and saves the file."""
        # Create the JSON, including the manipulation string we are using
        data = {'Manipulation': manip, **self.add_to_json(entries_labels=zip(labels, entries))}
        # Get the location to save the file
        path = self.file_save()
        # Save the .JSON
        with open(path, 'w') as f:
            f.write(json.dumps(data))

    def file_save(self):
        """Ask for where to save the JSON"""
        path_to_pref = filedialog.asksaveasfilename(
            defaultextension='.json', filetypes=[("json files", '*.json')],
            initialdir=self.default_path,
            title="Choose filename")
        if path_to_pref is None:    # asksaveasfile returns None if dialog closed with cancel
            return self.default_path + '.json'
        return path_to_pref

    def add_to_json(self, entries_labels: zip) -> dict:
        """Iterate through our labels/entries and add user information to the JSON file"""
        d = {}
        for (l, e) in entries_labels:
            # Get the text from the label and remove any trailing characters
            key = l.cget('text').strip(': ')
            # If the entry is a checkbutton, we need a specific command to get its value as a boolean
            if isinstance(e, tk.Checkbutton):
                if e.val.get() == 1:
                    d[key] = True
                else:
                    d[key] = False
            # If the entry is a slider, we need a specific command to get its value as a float
            elif isinstance(e, tk.Scale):
                d[key] = float(e.val.get())
            # Else, get the entry as either an integer or string
            elif isinstance(e, tk.Entry):
                try:
                    d[key] = int(e.get())
                except ValueError:
                    d[key] = str(e.get())
            elif isinstance(e, tk.Button):
                d[key] = self.filename
        return d

    def clear_out_windows(self):
        """Destroy any open toplevel windows (i.e. existing preset creation windows, graph windows...)"""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()

    def clear_out_widgets(self):
        """Clear out the widgets relating to any previously-selected manipulation"""
        self.manip_options.pack()
        for item in self.manip_options.winfo_children():
            item.pack_forget()
        self.filename = None
