import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
from PresetCreator import PresetCreator
import webbrowser
import json
import csv
import os
from random import shuffle


class ParentFrame:
    """Parent frame inherited by other GUI panes, includes methods for creating/organising tk widgets"""
    def __init__(self, **kwargs):
        # This is the root tk widget from which all panes are packed into
        self.root = kwargs.get('root')
        self.params = kwargs.get('params')
        self.keythread = kwargs.get('keythread')
        self.gui = kwargs.get('gui')
        # These two attributes are important: all GUI widgets should be placed within them so they can be packed
        self.tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.tk_list = []

    def organise_pane(self, col_num=1, px=10, py=1):
        """Organise all the widgets in the pane into the GUI"""
        for row_num, b in enumerate(self.tk_list):
            b.grid(row=row_num, column=col_num, padx=px, pady=py)

    # TODO: this should probably be deprecated at some point
    def populate_class(self, manip_str: str, arg=None,) -> list:
        """Populates the tk_list with buttons according to a certain manip string"""
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

    def get_tk_entry(self, t1='Default', t2='ms') -> tuple[tk.Frame, tk.Entry, tk.Label]:
        """Creates a frame with own Label-Entry-Label widgets, with customisable text. Frame must be in tk_list"""
        # Create the frame - this will need to be included in tk_list
        frame = tk.Frame(self.tk_frame)
        # Creates the widgets inside the frame, according to the text provided: these don't need to be gridded
        label = tk.Label(frame, text=t1)
        entry = tk.Entry(frame, width=5)
        ms = tk.Label(frame, text=t2)
        # Grid the widgets
        label.grid(row=1, column=1)
        entry.grid(row=1, column=2)
        ms.grid(row=1, column=3)
        # Return the frame (for including in tk_list), the entry (so values can be got), and the label
        return frame, entry, label

    @staticmethod
    def try_get_entry(entry: tk.Entry) -> int | None:
        """Takes a single entry widget and tries to get an integer value from it"""
        # Can get an integer value, so return it
        try:
            return int(entry.get())
        # Can't get an integer value, so replace anything in the entry with NaN and return None
        except ValueError:
            entry.delete(0, 'end')
            entry.insert(0, 'NaN')
            return None


class FlipPane(ParentFrame):
    """Flips the performer's video. This is mostly useful for testing that manipulations are working."""
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

    def init_labels(self) -> list:
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

    def init_logging_window(self) -> tk.scrolledtext.ScrolledText:
        log = tk.scrolledtext.ScrolledText(self.tk_frame, height=5, width=30,
                                           state='disabled', wrap='word', font='TkDefaultFont')
        log.insert('end', 'Started')
        return log


class CommandPane(ParentFrame):
    """This pane is used to control the central functionality of the program, e.g. starting/stopping recording"""
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        # These frames and entries are used to enter desired BPM and number of bars to count-in by
        bpm_frame, self.bpm_entry = self.init_bpm_entry()
        # Store all widgets in a list
        self.tk_list = [
            tk.Label(self.tk_frame, text='Commands'),
            tk.Button(self.tk_frame, text='Start Recording',
                      command=lambda: self.keythread.start_recording(bpm=self.try_get_entry(self.bpm_entry))),
            tk.Button(self.tk_frame, text='Stop Recording', command=self.keythread.stop_recording),
            bpm_frame,
            tk.Button(self.tk_frame, text="Reset", command=self.keythread.reset_manips),
            tk.Button(self.tk_frame, text='Info', command=self.init_info_popup),
            tk.Button(self.tk_frame, text="Quit", command=self.keythread.exit_loop),
        ]
        # Pack all the widgets in our list into the frame
        self.organise_pane()

    # TODO: would be nice to add some more info here - to do with Reaper?
    def init_info_popup(self):
        """Creates a tk messagebox showing information e.g. number of active cameras, fps, resolution..."""
        # Format the screen resolution by getting info from the params file
        p_res = 'x'.join([str(round(int(i) * self.params['*scaling'])) for i in self.params['*resolution'].split('x')])
        # Create the messagebox
        _ = tk.messagebox.showinfo(
            title='Info',
            message=f'Active cameras: {str(self.params["*participants"])}\n'
                    f'Camera FPS: {str(self.params["*fps"])}\n'
                    f'Researcher Camera Resolution: {self.params["*resolution"]}\n'
                    f'Performer Camera Resolution: {p_res}'
        )

    def init_bpm_entry(self) -> tuple[tk.Frame, tk.Entry]:
        """Returns frame/entry used to enter desired BPM value for recording"""
        bpm_frame, bpm_entry, _ = self.get_tk_entry(t1='Tempo:', t2='BPM')
        bpm_entry.insert('end', self.params['*default bpm'])
        return bpm_frame, bpm_entry


class ManipChoicePane(ParentFrame):
    """This pane is used to select a manipulation to be packed into the GUI"""
    def __init__(self, **kwargs):
        # Inherit from parent class
        super().__init__(**kwargs)
        self.combo = self.init_combo()
        self.tk_list = [tk.Label(self.tk_frame, text='Manipulations'), self.combo]
        self.organise_pane()

    def init_combo(self) -> ttk.Combobox:
        """Returns a combobox filled with the available manipulations listed in TkGui, creates pane when selected"""
        # Fill the combobox options with the possible manipulations
        combo = ttk.Combobox(self.tk_frame, state='readonly', values=[k for k in self.gui.manip_panes.keys()])
        combo.set('Choose a Manipulation')
        # Create the necessary pane whenever a new manipulation is selected
        combo.bind("<<ComboboxSelected>>",
                   lambda e: self.gui.add_manip_to_root(pane=self.gui.manip_panes[combo.get()]))
        # Return the combobox so it can be added to the list and packed
        return combo


class PausePane(ParentFrame):
    """Enables the user to pause the video and audio feedback participants receive"""
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

    # TODO: do these all need to be functions? can we define them in __init__?
    def init_pause_audio(self) -> tk.Button:
        """Pause the audio in reathread"""
        b = tk.Button(
            self.tk_frame, text='Pause Audio', fg='black', command=lambda: [
                self.keythread.enable_manip('pause audio', b),
                self.keythread.reathread.pause_manip()
            ]
        )
        return b

    def init_pause_video(self) -> tk.Button:
        """Pause the video in all the camthreads"""
        b = tk.Button(
            self.tk_frame, text='Pause Video', fg='black', command=lambda: [
                self.keythread.enable_manip('pause video', b)
            ]
        )
        return b

    def init_pause_both(self) -> tk.Button:
        """Pause both the audio and video"""
        b = tk.Button(
            self.tk_frame, text='Pause Both', fg='black', command=lambda: [
                self.keythread.enable_manip('pause video', b),
                self.keythread.reathread.pause_manip()
            ]
        )
        return b


# TODO: ensure that audio can be looped as well!
class LoopPane(ParentFrame):
    """Enables the user to loop a portion of video and play it back again later"""
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
    """Allows the user to create and load in presets as .JSON files"""
    def __init__(self, **kwargs):
        """This class creates a pane in TkGui that enables the user to load and create manipulation presets"""
        # Inherit from parent class
        super().__init__(**kwargs)
        # Initialise basic parameters
        self.presets_dir = './input/'
        self.presets_list = []
        self.default_path = './output/'
        self.selected_preset = None
        # Initialise the preset selector listbox
        self.presets_listbox = PresetListbox(tk_frame=self.tk_frame, presetpane=self)
        # These widgets should be packed in TkGui
        self.tk_list = [
            tk.Label(self.tk_frame, text='Presets'),
            tk.Button(self.tk_frame, text="Open Preset Creator", command=self.open_preset_creator),
            tk.Button(self.tk_frame, text="Load Preset Folder", command=self.open_preset_folder),
            self.presets_listbox,
            self.add_remove_shift_presets_buttons(),
            tk.Button(self.tk_frame, text='Randomise Presets', command=self.randomise_presets),
            tk.Button(self.tk_frame, text='Save Preset Order', command=self.save_preset_order),
        ]
        self.organise_pane()

    def add_remove_shift_presets_buttons(self):
        f = tk.Frame(self.tk_frame)
        li = [
            tk.Button(f, text='+', command=self.add_preset_from_file),
            tk.Button(f, text='-', command=self.remove_preset),
            tk.Button(f, text='▲', command=lambda: self.move_preset_button(shift=-1)),
            tk.Button(f, text='▼', command=lambda: self.move_preset_button(shift=1)),
            tk.Button(f, text='Clear', command=self.clear_presets)
        ]
        for num, b in enumerate(li):
            b.grid(column=num, row=0)
        return f

    def open_preset_folder(self):
        """Prompts for the user to select a directory to search for valid preset files in"""
        # Open the directory
        f = filedialog.askdirectory(title='Open presets folder', initialdir=self.presets_dir,)
        # Tk askdirectory returns None if dialog closed with cancel
        if f == '':
            return
        # If a valid directory has been selected, try and get jsons from it
        else:
            self.presets_dir = f
            self.get_jsons_from_dir()

    def add_preset_from_file(self):
        # Open the directory
        js = filedialog.askopenfilename(title='Open preset file', initialdir=self.presets_dir,)
        fname = os.path.basename(js)
        # If we've opened a JSON file
        if js.endswith('.json'):
            # Load the JSON file and read
            f = json.loads(open(js, 'r').read())
            # Add the json filename as a parameter to the dictionary we just created
            f['JSON Filename'] = fname.removesuffix('.json')
            # Add the json to the preset list if it is valid
            if self.check_json(js=f):
                self.presets_list.append(f)
                self.populate_preset_listbox()
        else:
            self.gui.log_text(f'File {fname} is not a .json file')

    def get_jsons_from_dir(self):
        """Searches through a directory for preset files and adds them to a list if they're valid"""
        # Reset the presets list and listbox to neutral
        self.clear_presets()
        # Get all the json files in our directory
        jsons = [f for f in os.listdir(self.presets_dir) if f.endswith('.json')]
        # Iterate through our json files and add those that are valid to our preset list
        self.iterate_through_jsons(jsons)
        # We only want to update the functionality of our combobox if valid presets have been loaded
        if len(self.presets_list) > 0:
            self.populate_preset_listbox()

    def iterate_through_jsons(self, jsons):
        """Iterate through our json files and add those that are valid to our preset list"""
        for js in jsons:
            # Load in the json
            f = json.loads(open(self.presets_dir + '/' + js, 'r').read())
            # Add the json filename as a parameter to the dictionary we just created
            f['JSON Filename'] = js.removesuffix('.json')
            # Add the json to the preset list if it is valid
            if self.check_json(js=f):
                self.presets_list.append(f)

    def check_json(self, js: dict):
        """Checks if a particular json file contains valid information for the application"""
        # This key should always be present in any valid .JSON made for use with this software
        if 'Manipulation' not in js:
            return False
        # Discard if we've already added the JSON
        if any(p['JSON Filename'] == js['JSON Filename'] for p in self.presets_list):
            self.gui.log_text('Duplicate preset added, discarded...')
            return False
        # TODO: Add more checks in here: disabled for now for ease of using Delay From File presets
        # If the user entered nothing in a field, discard the JSON
        if any(v == '' for v in js.values()):
            return False
        # If the json passes the above checks, it is valid
        else:
            return True

    def clear_presets(self):
        self.presets_list.clear()
        self.presets_listbox.clear_listbox()

    def populate_preset_listbox(self):
        """Populates the preset listbox with valid preset files"""
        # Format the string to display in the combobox, including the json filename & preset number
        presets = [f'{k["JSON Filename"]}, {k["Manipulation"]}' for k in self.presets_list]
        # Clear the listbox out
        self.presets_listbox.clear_listbox()
        # Populate the listbox with the new functionality
        self.presets_listbox.populate_listbox(presets=presets)

    def preset_selected(self, selected):
        """Opens the selected preset pane in the GUI"""
        if len(self.presets_list) > 0:
            self.selected_preset = self.presets_list[selected]
            self.gui.preset_handler(self.selected_preset)

    def open_preset_creator(self):
        """Creates a new toplevel window to allow the user to create preset files"""
        pc = PresetCreator(root=self.root)
        pc.create_window()

    def randomise_presets(self):
        """Shuffles the loaded presets and populates the combobox with the new list"""
        # We don't want to shuffle if we haven't loaded any presets in yet!
        if len(self.presets_list) > 0:
            shuffle(self.presets_list)
            self.populate_preset_listbox()
        # If we haven't loaded in any presets, reset the combobox for safety
        else:
            self.presets_listbox.clear_listbox()

    def save_preset_order(self):
        """Saves the order of loaded in presets to a .csv file"""
        # Convert the current order of presets to a .csv file
        to_csv = self.preset_order_to_csv()
        # Prompt for a location to save the .csv
        save_dir = self.csv_file_save()
        # Save the .csv file
        try:
            output_file = open(save_dir, 'w', newline='')
            dict_writer = csv.DictWriter(output_file, list(to_csv[0].keys()))
            dict_writer.writeheader()
            dict_writer.writerows(to_csv)
        except FileNotFoundError:
            self.gui.log_text('No file selected')
        except FileExistsError:
            self.gui.log_text('File already exists')
        except IndexError:
            self.gui.log_text('No presets added')
        else:
            self.gui.log_text('')

    def preset_order_to_csv(self):
        """Iterate through the presets list and generate the lines for the .csv file"""
        to_csv = []
        for (num, preset) in enumerate(self.presets_list):
            dic = {
                'Preset Number': num,
                'JSON': preset
            }
            to_csv.append(dic)
        return to_csv

    def csv_file_save(self):
        """Ask for where to save the .csv preset order"""
        path_to_pref = filedialog.asksaveasfilename(
            defaultextension='.csv', filetypes=[("csv files", '*.csv')],
            initialdir=self.default_path,
            title="Choose filename"
        )
        if path_to_pref is None:    # asksaveasfile returns None if dialog closed with cancel
            return self.default_path + '.csv'
        return path_to_pref

    def shift_preset_list(self, selected, index):
        """Readjust the underlying presets list when presets are dragged-dropped in the listbox"""
        self.presets_list.remove(selected)
        self.presets_list.insert(index, selected)

    def remove_preset(self):
        """Removes the selected preset from the listbox"""
        # Try and remove the selected element from the preset list
        try:
            self.presets_list.pop(self.presets_listbox.cur_index)
        # If an element isn't selected, cur_index will return None - so need to catch error
        except IndexError:
            pass
        finally:
            # Refresh the listbox if there are still presets in our presets_list
            if len(self.presets_list) > 0:
                self.populate_preset_listbox()
            # Else, clear the listbox and remove its functionality
            elif len(self.presets_list) == 0:
                self.presets_listbox.clear_listbox()

    def move_preset_button(self, shift):
        """Moves presets using buttons"""
        old_i = self.presets_list.index(self.presets_list[self.presets_listbox.cur_index])
        shifted = old_i + shift
        # Only move if it won't remove the element from the list
        if 0 <= shifted < len(self.presets_list):
            self.presets_list.insert(old_i + shift, self.presets_list.pop(old_i))
            x = self.presets_listbox.get(old_i)
            self.presets_listbox.delete(old_i)
            self.presets_listbox.insert(old_i + shift, x)
            self.presets_listbox.cur_index += shift
            self.presets_listbox.activate(self.presets_listbox.cur_index)

    def return_current_preset(self):
        return self.selected_preset


class PresetListbox(tk.Listbox):
    """A listbox holding loaded loaded presets with drag and drop reordering of entries."""
    def __init__(self, tk_frame, presetpane, **kw):
        kw['selectmode'] = tk.SINGLE
        tk.Listbox.__init__(self, tk_frame, kw)
        self.presetpane = presetpane
        self.cur_index = 1
        self.clear_listbox()

    def reset_listbox_func(self):
        """Reset the functionality of the listbox if no presets have been loaded"""
        self.bind('<Button-1>',)
        self.bind('<Double-Button-1>',)
        self.bind('<B1-Motion>',)


    def init_listbox_func(self):
        """If presets have been loaded, bind the correct functionality to the listbox"""
        self.bind('<Button-1>', self.set_current)
        self.bind('<Double-Button-1>', self.make_active)
        # self.bind('<B1-Motion>', self.shift_selection_drag)

    def set_current(self, event):
        """Set the current index whenever a listbox element is clicked on"""
        self.cur_index = self.nearest(event.y)
        self.activate(self.cur_index)

    def make_active(self, event):
        """Make the selected preset active in the GUI whenever it is double-clicked on"""
        self.cur_index = self.nearest(event.y)
        self.presetpane.preset_selected(self.cur_index)

    def shift_selection_drag(self, event):
        """Allows the user to rearrange listbox elements by dragging and dropping them"""
        i = self.nearest(event.y)
        # Get the selected element from the presets list
        selected = self.presetpane.presets_list[self.cur_index]
        if i < self.cur_index:
            x = self.get(i)
            self.delete(i)
            self.insert(i + 1, x)
            self.cur_index = i
        elif i > self.cur_index:
            x = self.get(i)
            self.delete(i)
            self.insert(i - 1, x)
            self.cur_index = i
        self.presetpane.shift_preset_list(selected=selected, index=self.cur_index)

    def clear_listbox(self):
        """Clear the listbox and reset its functionality"""
        self.reset_listbox_func()
        self.delete(0, 'end')
        self.insert(0, 'No presets loaded!')
        self.set_listbox_apperance()

    def populate_listbox(self, presets: list):
        """Enable the listbox functionality and fill it with presets"""
        self.init_listbox_func()
        self.delete(0, 'end')
        # Iterate through the list of presets
        for num, preset in enumerate(presets):
            self.insert(num, preset)
        self.set_listbox_apperance()

    def set_listbox_apperance(self):
        """Scale the listbox appearance to match the number of entries"""
        self.config(width=0, height=0)
