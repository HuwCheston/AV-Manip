import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
from PresetCreator import PresetCreator
import webbrowser
import json
import os


class ParentFrame:
    def __init__(self, **kwargs):
        self.root = kwargs.get('root')
        self.params = kwargs.get('params')
        self.keythread = kwargs.get('keythread')
        self.gui = kwargs.get('gui')
        self.tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.tk_list = []

    def organise_pane(self, col_num=1, px=10, py=1):
        for row_num, b in enumerate(self.tk_list):
            b.grid(row=row_num, column=col_num, padx=px, pady=py)

    def populate_class(self, manip_str, arg=None,):
        lis = []
        for k in self.params.keys():
            if k.startswith(manip_str):
                b = tk.Button(self.tk_frame, text=k.title())
                if arg is not None:
                    b.config(fg='black',
                             command=lambda manip=k, button=b: [self.keythread.enable_manip(manip, button), arg()])
                else:
                    b.config(fg='black', command=lambda manip=k, button=b: [self.keythread.enable_manip(manip, button)])
                lis.append(b)
        return lis

    def get_tk_entry(self, t1='Default', t2='ms'):
        frame = tk.Frame(self.tk_frame)
        label = tk.Label(frame, text=t1)
        entry = tk.Entry(frame, width=5)
        ms = tk.Label(frame, text=t2)
        label.grid(row=1, column=1)
        entry.grid(row=1, column=2)
        ms.grid(row=1, column=3)
        return frame, entry, label

    @staticmethod
    def try_get_entry(entry: tk.Entry):
        """
        This function takes a single tk entry and tries to get an integer value from it. If an integer value can be
        obtained, it is returned. Otherwise, any value in the entry is deleted and replaced with NaN, and the function
        returns None.
        :param entry:
        :return:
        """

        # Can get an integer value, so return it
        try:
            return int(entry.get())
        # Can't get an integer value, so replace anything in the entry with NaN and return None
        except ValueError:
            entry.delete(0, 'end')
            entry.insert(0, 'NaN')
            return None


class FlipPane(ParentFrame):
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        # Store all widgets in a list
        b_list = self.populate_class(manip_str='flip',)
        self.tk_list = [i for sublist in [[tk.Label(self.tk_frame, text='Flip')], b_list] for i in sublist]
        # Pack all the widgets in our list into the frame
        self.organise_pane()


class InfoPane(ParentFrame):
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        # We want this frame to look different to the others, so let's override the parent tk_frame attribute
        self.tk_frame = tk.Frame(self.root, padx=10, pady=1)
        self.logging_window = self.init_logging_window()
        self.tk_list = [i for sublist in [self.init_labels(), [self.logging_window]] for i in sublist]
        self.organise_pane(px=0, py=0)

    def init_labels(self):
        labels = [
            '',
            'AV-Manip (v.0.1)',
            '© Huw Cheston, 2022'
        ]
        urls = [
            "https://cms.mus.cam.ac.uk/",
            'https://github.com/HuwCheston/AV-Manip/',
            'https://github.com/HuwCheston/',
        ]

        lablist = []
        for (label, url) in zip(labels, urls):
            lab = tk.Label(self.tk_frame, text=label)
            lab.bind('<Button-1>', lambda e, u=url: webbrowser.open_new(u))
            if lab['text'] == '':
                lab.image = tk.PhotoImage(file="cms-logo.gif")
                lab['image'] = lab.image
            lablist.append(lab)
        return lablist

    def init_logging_window(self):
        log = tk.scrolledtext.ScrolledText(self.tk_frame, height=5, width=20,
                                           state='disabled', wrap='word', font='TkDefaultFont')
        log.insert('end', 'Started')
        return log


class CommandPane(ParentFrame):
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        # These frames and entries are used to enter desired BPM and number of bars to count-in by
        bpm_frame, bpm_entry = self.init_bpm_entry()
        # Store all widgets in a list
        self.tk_list = [
            tk.Label(self.tk_frame, text='Commands'),
            tk.Button(self.tk_frame, text='Start Recording',
                      command=lambda: self.keythread.start_recording(bpm=self.try_get_entry(bpm_entry))),
            tk.Button(self.tk_frame, text='Stop Recording', command=self.keythread.stop_recording),
            bpm_frame,
            tk.Button(self.tk_frame, text="Reset", command=self.keythread.reset_manips),
            tk.Button(self.tk_frame, text='Info', command=self.init_info_popup),
            tk.Button(self.tk_frame, text="Quit", command=self.keythread.exit_loop),
        ]
        # Pack all the widgets in our list into the frame
        self.organise_pane()

    def init_info_popup(self):
        # Format the screen resolution by getting info from the params file
        p_res = 'x'.join([str(round(int(i) * self.params['*scaling'])) for i in self.params['*resolution'].split('x')])
        # Create the messagebox
        message = tk.messagebox.showinfo(title='Info',
                                         message=f'Active cameras: {str(self.params["*participants"])}\n'
                                                 f'Camera FPS: {str(self.params["*fps"])}\n'
                                                 f'Researcher Camera Resolution: {self.params["*resolution"]}\n'
                                                 f'Performer Camera Resolution: {p_res}')
        return message

    def init_bpm_entry(self):
        bpm_frame, bpm_entry, _ = self.get_tk_entry(t1='Tempo:', t2='BPM')
        bpm_entry.insert('end', self.params['*default bpm'])
        return bpm_frame, bpm_entry


class ManipChoicePane(ParentFrame):
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        self.tk_list = [tk.Label(self.tk_frame, text='Manipulations'), self.init_combo()]
        self.organise_pane()

    def init_combo(self):
        # Fill the combobox options with the possible manipulations
        combo = ttk.Combobox(self.tk_frame, state='readonly', values=[k for k in self.gui.manip_panes.keys()])
        combo.set('Choose a Manipulation')
        # Create the necessary pane whenever a new manipulation is selected
        combo.bind("<<ComboboxSelected>>",
                   lambda e: self.gui.add_manip_to_frame(pane=self.gui.manip_panes[combo.get()]))
        # Return the combobox so it can be added to the list and packed
        return combo


class PausePane(ParentFrame):
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        # Store all widgets in a list
        self.tk_list = [
            tk.Label(self.tk_frame, text='Pause'),
            # We need to call these as functions so we can pass them back into themselves
            self.init_pause_audio(),
            self.init_pause_video(),
            self.init_pause_both(),
        ]
        # Pack all the widgets in our list into the frame
        self.organise_pane()

    def init_pause_audio(self):
        b = tk.Button(
            self.tk_frame, text='Pause Audio', fg='black', command=lambda: [
                self.keythread.enable_manip('pause audio', b),
                self.keythread.reathread.pause_manip()
            ]
        )
        return b

    def init_pause_video(self):
        b = tk.Button(
            self.tk_frame, text='Pause Video', fg='black', command=lambda: [
                self.keythread.enable_manip('pause video', b)
            ]
        )
        return b

    def init_pause_both(self):
        b = tk.Button(
            self.tk_frame, text='Pause Both', fg='black', command=lambda: [
                self.keythread.enable_manip('pause video', b),
                self.keythread.reathread.pause_manip()
            ]
        )
        return b


class LoopPane(ParentFrame):
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        # Store all widgets in a list
        b_list = self.populate_class(manip_str='loop',)
        self.tk_list = [i for sublist in [[tk.Label(self.tk_frame, text='Looper')], b_list] for i in sublist]
        # Pack all the widgets in our list into the frame
        self.organise_pane()


class BlankPane(ParentFrame):
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        # Store all widgets in a list
        b_list = self.populate_class(manip_str='blank',)
        self.tk_list = [i for sublist in [[tk.Label(self.tk_frame, text='Flip')], b_list] for i in sublist]
        # Pack all the widgets in our list into the frame
        self.organise_pane()


class ControlPane(ParentFrame):
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        # Store all widgets in a list
        b_list = self.populate_class(manip_str='control')
        self.tk_list = [i for sublist in [[tk.Label(self.tk_frame, text='Flip')], b_list] for i in sublist]
        # Pack all the widgets in our list into the frame
        self.organise_pane()


class PresetPane(ParentFrame):
    def __init__(self, **kwargs):
        """This class creates a pane in TkGui that enables the user to load and create manipulation presets"""
        # Inherit from parent class
        super().__init__(**kwargs)
        # Initialise basic parameters
        self.presets_dir = './input/'
        self.presets_list = []
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
        self.organise_pane()

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
