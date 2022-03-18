import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from DelayPanes import VariableDelay, IncrementalDelay, FixedDelay, DelayFromFile, get_tk_entry, try_get_entry
from PresetCreator import PresetPane
import webbrowser
import itertools


class TkGui:
    def __init__(self, params, keythread):
        self.root = tk.Tk()
        self.root.title('AV-Manip')
        self.root.attributes('-topmost', 'true')
        self.root.iconbitmap("cms-logo.ico")
        self.logging_window = None
        self.file_delay = None

        self.params = params
        self.keythread = keythread
        self.tk_list = []
        self.buttons_list = []

        self.active_panes = [
            self.info_pane,
            self.command_pane,
            self.preset_pane,
            self.manip_choice_pane,
        ]

        self.manip_panes = {
            'Fixed Delay': self.fixed_delay_pane,
            'Delay from File': self.delay_from_file_pane,
            'Variable Delay': self.variable_delay_pane,
            'Incremental Delay': self.moving_delay_pane,
            'Loop Audio/Video': self.loop_pane,
            'Pause Audio/Video': self.pause_pane,
            'Blank Video': self.blank_pane,
            'Control Audio': self.control_pane,
            'Flip Video': self.flip_pane
        }

    def tk_setup(self):
        # TODO: why does this need to be num+1?
        for widget in self.root.winfo_children():
            widget.destroy()
        for (num, pane) in enumerate(self.active_panes):
            pane(col_num=num + 1)

    def command_pane(self, col_num):
        command_pane = CommandPane(root=self.root, col_num=col_num, keythread=self.keythread, params=self.params)
        command_pane.tk_frame.grid(column=col_num, row=1, sticky='n', padx=10, pady=10)

    def info_pane(self, col_num):
        info_pane = InfoPane(root=self.root, col_num=col_num)
        self.logging_window = info_pane.logging_window
        info_pane.tk_frame.grid(column=col_num, row=1, sticky='n', padx=10, pady=10)

    def preset_pane(self, col_num):
        preset_pane = PresetPane(root=self.root)
        organise_pane(tk_list=preset_pane.tk_list, col_num=col_num)
        preset_pane.tk_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)

    def manip_choice_pane(self, col_num):
        choice_frame = tk.Frame(self.root, borderwidth=2, relief="groove")

        # Fill the combobox options with the possible manipulations
        combo = ttk.Combobox(choice_frame, state='readonly', values=[k for k in self.manip_panes.keys()])
        combo.set('Choose a Manipulation')
        # Create the necessary pane whenever a new manipulation is selected
        combo.bind("<<ComboboxSelected>>", lambda e: self.insert_new_pane(self.manip_panes[combo.get()]))

        choice_tk_list = [tk.Label(choice_frame, text='Manipulations'), combo]
        choice_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=choice_tk_list, col_num=col_num)

    def insert_new_pane(self, pane):
        # TODO: this function should allow any pane to open - should clear the decks a bit!
        self.keythread.reset_manips()
        try:
            del self.active_panes[4]
        except IndexError:
            pass
        self.active_panes.append(pane)
        self.tk_setup()

    def fixed_delay_pane(self, col_num):
        fixed_delay = FixedDelay(params=self.params, root=self.root, keythread=self.keythread, gui=self)
        fixed_delay.delay_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=fixed_delay.tk_list, col_num=col_num)
        self.buttons_list.append(fixed_delay.start_delay_button)

    def delay_from_file_pane(self, col_num):
        self.file_delay = DelayFromFile(params=self.params, root=self.root, keythread=self.keythread, gui=self)
        self.file_delay.delay_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=self.file_delay.tk_list, col_num=col_num)
        self.buttons_list.append(self.file_delay.start_delay_button)

    def variable_delay_pane(self, col_num):
        variable_delay = VariableDelay(params=self.params, root=self.root, keythread=self.keythread, gui=self)
        variable_delay.delay_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=variable_delay.tk_list, col_num=col_num)
        self.buttons_list.append(variable_delay.start_delay_button)

    def moving_delay_pane(self, col_num):
        moving_delay = IncrementalDelay(params=self.params, root=self.root, keythread=self.keythread, gui=self)
        moving_delay.delay_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=moving_delay.tk_list, col_num=col_num)
        self.buttons_list.append(moving_delay.start_delay_button)

    def loop_pane(self, col_num):
        manip_str = 'loop'
        self.populate_tk_list(manip_str, col_num=col_num)

    def blank_pane(self, col_num):
        manip_str = 'blank'
        self.populate_tk_list(manip_str, col_num=col_num)

    def pause_pane(self, col_num):
        frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        pause_audio = tk.Button(frame, text='Pause Audio', fg='black',
                                command=lambda: [self.keythread.enable_manip('pause audio', pause_audio),
                                                 self.keythread.reathread.pause_manip()])
        self.buttons_list.append(pause_audio)

        pause_video = tk.Button(frame, text='Pause Video', fg='black')
        pause_video.config(command=lambda: self.keythread.enable_manip('pause video', pause_video))
        self.buttons_list.append(pause_video)

        pause_both = tk.Button(frame, text='Pause Both', fg='black')
        pause_both.config(command=lambda: [self.keythread.enable_manip('pause video', pause_both),
                                           self.keythread.reathread.pause_manip()])
        self.buttons_list.append(pause_both)

        tk_list = [
            tk.Label(frame, text='Pause'),
            pause_audio,
            pause_video,
            pause_both
        ]
        frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=tk_list, col_num=col_num)
        self.tk_list.extend(tk_list)

    def control_pane(self, col_num):
        manip_str = 'control'
        self.populate_tk_list(manip_str, col_num=col_num)

    def flip_pane(self, col_num):
        manip_str = 'flip'
        self.populate_tk_list(manip_str, col_num=col_num)

    def populate_tk_list(self, manip_str, col_num, arg=None):
        frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        tk_list = [tk.Label(frame, text=manip_str.title())]
        for k in self.params.keys():
            if k.startswith(manip_str):
                b = tk.Button(frame, text=k.title())
                b.config(fg='black', command=lambda manip=k, button=b: [self.keythread.enable_manip(manip, button),
                                                                        arg()])
                tk_list.append(b)
                self.buttons_list.append(b)
        organise_pane(tk_list=tk_list, col_num=col_num)
        frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        self.tk_list.extend(tk_list)

    def log_text(self, text):
        self.logging_window.config(state='normal')
        self.logging_window.insert('end', '\n' + text)
        self.logging_window.see("end")
        self.logging_window.config(state='disabled')


class InfoPane:
    def __init__(self, root, col_num):
        self.root = root
        self.tk_frame = tk.Frame(self.root, padx=10, pady=1)
        self.logging_window = self.init_logging_window()
        self.tk_list = [i for sublist in [self.init_labels(), [self.logging_window]] for i in sublist]
        organise_pane(tk_list=self.tk_list, col_num=col_num, px=0, py=0)

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


class CommandPane:
    def __init__(self, root, params, keythread, col_num):
        self.root = root
        self.tk_frame = tk.Frame(self.root, padx=10, pady=1)
        self.params = params
        self.keythread = keythread

        # Master frame for this pane (all other widgets should use this as their root)
        self.tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        # These frames and entries are used to enter desired BPM and number of bars to count-in by
        bpm_frame, bpm_entry = self.init_bpm_entry()

        self.tk_list = [
            tk.Label(self.tk_frame, text='Commands'),
            tk.Button(self.tk_frame, text='Start Recording',
                      command=lambda: self.keythread.start_recording(bpm=try_get_entry(bpm_entry))),
            tk.Button(self.tk_frame, text='Stop Recording', command=self.keythread.stop_recording),
            bpm_frame,
            tk.Button(self.tk_frame, text="Reset", command=self.keythread.reset_manips),
            tk.Button(self.tk_frame, text='Info', command=self.init_info_popup),
            tk.Button(self.tk_frame, text="Quit", command=self.keythread.exit_loop),
        ]
        organise_pane(tk_list=self.tk_list, col_num=col_num)

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
        bpm_frame, bpm_entry, _ = get_tk_entry(frame=self.tk_frame, t1='Tempo:', t2='BPM')
        bpm_entry.insert('end', self.params['*default bpm'])
        return bpm_frame, bpm_entry


def organise_pane(tk_list, col_num, px=10, py=1):
    for row_num, b in enumerate(tk_list):
        b.grid(row=row_num, column=col_num, padx=px, pady=py)
