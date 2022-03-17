import tkinter as tk
from tkinter import ttk, filedialog
import json


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


class PresetCreator:
    def __init__(self, root):
        # Initialise basic class parameters
        self.root = root
        self.manip_list = manip_names
        self.filename = ''
        self.default_path = './input/'

        # Initialise new top level window with required attributes
        self.creator_window = tk.Toplevel(self.root)
        self.creator_window.title('Preset Creator')
        self.creator_window.geometry("%dx%d%+d%+d" % (300, 300, 250, 125))
        self.creator_window.attributes('-topmost', 'true')
        self.creator_window.iconbitmap("cms-logo.ico")

        # Widgets created here will not be cleared whenever a new manipulation is selected - e.g. combobox, file name...
        self.creator_frame = tk.Frame(self.creator_window, borderwidth=2, relief="groove")
        _ = tk.Label(self.creator_frame, text='Preset Creator').pack()
        _ = tk.Label(self.creator_frame,
                     text='Use this tool to create preset .JSON files').pack()
        self.creator_frame.pack(padx=10, pady=10, anchor='center')

        # Widgets created here will be cleared whenever a new manipulation is selected - these are the parameters
        self.manip_options = tk.Frame(self.creator_frame)

    def choose_manip(self):
        combo = ttk.Combobox(self.creator_frame, state='readonly',
                             values=[k for k in self.manip_list.keys()])
        combo.set('Choose a Manipulation')
        combo.bind("<<ComboboxSelected>>", lambda e: self.manip_selected(combo.get()))
        combo.pack(padx=1, pady=3, anchor='center')

    def manip_selected(self, manip):
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
        submit.pack(padx=1, pady=3, anchor='center')

    @staticmethod
    def preset_labels(d: dict, frames: list) -> list:
        labels = []
        for num, lab in enumerate(d.keys()):
            w = tk.Label(frames[num], text=lab + ': ')
            labels.append(w)
            w.grid(column=1, row=1, sticky="n", padx=1, pady=3)
        return labels

    def preset_entries(self, d: dict, frames: list) -> list:
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
                w = tk.Button(frames[num], command=self.open_file, text='Open File')
            elif ty == 'int':
                w = tk.Entry(frames[num], validate="key", width=5)
                # This command prevents us from inserting anything other than numbers
                w['validatecommand'] = (w.register(self.validate_int), '%P', '%d')
                # Create a label after the entry indicating the unit
                _ = tk.Label(frames[num], text='ms').grid(row=1, column=3, sticky="n", padx=1, pady=3)
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
            w.grid(column=2, row=1, sticky="n", padx=1, pady=3)
            entries.append(w)
        return entries

    @keep_focus
    def open_file(self):
        f = tk.filedialog.askopenfile(
            title='Open a file',
            initialdir='./input/',
            filetypes=(
                ('CSV files', '*.csv'),
                ('Text files', '*.txt'),
                ('All files', '*.*'),
            )
        )
        if f is None:   # askopenfile returns None if dialog closed with cancel
            return
        self.filename = f.name

    @staticmethod
    def validate_int(s, acttyp) -> bool:
        if acttyp == '1':  # insert
            if not s.isdigit():
                return False
        return True

    @staticmethod
    def validate_float(s, acttyp) -> bool:
        if acttyp == '1':  # insert
            print(s)
            if s not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.']:
                return False
        return True

    @keep_focus
    def submit_preset(self, labels: list, entries: list, manip: str):
        # Create the JSON, including the manipulation string we are using
        data = {'Manipulation': manip, **self.add_to_json(entries_labels=zip(labels, entries))}
        # Get the location to save the file
        path = self.file_save()
        # Save the .JSON
        with open(path, 'w') as f:
            f.write(json.dumps(data))

    def file_save(self):
        # Ask for where to save the JSON
        path_to_pref = filedialog.asksaveasfilename(
            defaultextension='.json', filetypes=[("json files", '*.json')],
            initialdir=self.default_path,
            title="Choose filename")
        if path_to_pref is None:    # asksaveasfile returns None if dialog closed with cancel
            return self.default_path
        return path_to_pref

    def add_to_json(self, entries_labels: zip) -> dict:
        # Iterate through our labels/entries and add to the JSON file
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

    def clear_out_widgets(self):
        self.manip_options.pack()
        for item in self.manip_options.winfo_children():
            item.pack_forget()
