import tkinter as tk
from tkinter import messagebox, scrolledtext
from DelayPanes import VariableDelay, IncrementalDelay, FixedDelay, DelayFromFile
import webbrowser


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

        self.panes = [
            self.info_pane,
            self.command_pane,
            self.fixed_delay_pane,
            self.variable_delay_pane,
            self.moving_delay_pane,
            self.delay_from_file_pane,
            self.loop_pane,
            self.pause_pane,
            self.blank_pane,
            self.control_pane,
            self.flip_pane
        ]

    def tk_setup(self):
        # TODO: why does this need to be num+1?
        for num, pane in enumerate(self.panes):
            pane(col_num=num + 1)

    def info_pane(self, col_num):
        info_frame = tk.Frame(self.root, padx=10, pady=1)
        labels = {
            tk.Label(info_frame, text='CMS logo'): lambda e: webbrowser.open_new(
                "https://cms.mus.cam.ac.uk/"),
            tk.Label(info_frame, text='AV-Manip (v.0.1)'): lambda e: webbrowser.open_new(
                'https://github.com/HuwCheston/AV-Manip/'),
            tk.Label(info_frame, text='© Huw Cheston, 2022'): lambda e: webbrowser.open_new(
                'https://github.com/HuwCheston/'),
        }
        for (label, func) in labels.items():
            label.bind('<Button-1>', func)
            if label['text'] == 'CMS logo':
                label.image = tk.PhotoImage(file="cms-logo.gif")
                label['image'] = label.image
        self.logging_window = tk.scrolledtext.ScrolledText(info_frame, height=5, width=20, state='disabled',
                                                           wrap='word', font='TkDefaultFont')
        self.logging_window.insert('end', 'Started')
        labels[self.logging_window] = None
        organise_pane(tk_list=labels, col_num=col_num, px=0, py=0)
        info_frame.grid(row=1, column=col_num)

    def command_pane(self, col_num):
        p_res = 'x'.join([str(round(int(i) * self.params['*scaling'])) for i in self.params['*resolution'].split('x')])
        command_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        command_tk_list = [
            tk.Label(command_tk_frame, text='Commands'),
            tk.Button(command_tk_frame, text="Reset", command=self.keythread.reset_manips),
            tk.Button(command_tk_frame, text='Info',
                      command=lambda:
                      tk.messagebox.showinfo(title='Info',
                                             message=f'Active cameras: {str(self.params["*participants"])}\n'
                                                     f'Camera FPS: {str(self.params["*fps"])}\n'
                                                     f'Researcher Camera Resolution: {self.params["*resolution"]}\n'
                                                     f'Performer Camera Resolution: {p_res}')),
            tk.Button(command_tk_frame, text="Quit", command=self.keythread.exit_loop),
        ]
        organise_pane(tk_list=command_tk_list, col_num=col_num)
        command_tk_frame.grid(column=2, row=1, sticky="n", padx=10, pady=10)

    # TODO: collapse these into a single function - a combobox that displays whichever delay type when selected
    def fixed_delay_pane(self, col_num):
        fixed_delay = FixedDelay(params=self.params, root=self.root, keythread=self.keythread, gui=self)
        fixed_delay.delay_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=fixed_delay.tk_list, col_num=col_num)
        self.tk_list.append(fixed_delay.start_delay_button)

    def delay_from_file_pane(self, col_num):
        self.file_delay = DelayFromFile(params=self.params, root=self.root, keythread=self.keythread, gui=self)
        self.file_delay.delay_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=self.file_delay.tk_list, col_num=col_num)
        self.tk_list.append(self.file_delay.start_delay_button)

    def variable_delay_pane(self, col_num):
        variable_delay = VariableDelay(params=self.params, root=self.root, keythread=self.keythread)
        variable_delay.delay_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=variable_delay.tk_list, col_num=col_num)
        self.tk_list.append(variable_delay.start_delay_button)

    def moving_delay_pane(self, col_num):
        moving_delay = IncrementalDelay(params=self.params, root=self.root, keythread=self.keythread, gui=self)
        moving_delay.delay_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        organise_pane(tk_list=moving_delay.tk_list, col_num=col_num)
        self.tk_list.append(moving_delay.start_delay_button)

    def loop_pane(self, col_num):
        manip_str = 'loop'
        self.populate_tk_list(manip_str, col_num=col_num)

    def blank_pane(self, col_num):
        manip_str = 'blank'
        self.populate_tk_list(manip_str, col_num=col_num)

    def pause_pane(self, col_num):
        manip_str = 'pause'
        self.populate_tk_list(manip_str, col_num=col_num)

    def control_pane(self, col_num):
        manip_str = 'control'
        self.populate_tk_list(manip_str, col_num=col_num)

    def flip_pane(self, col_num):
        manip_str = 'flip'
        self.populate_tk_list(manip_str, col_num=col_num)

    def populate_tk_list(self, manip_str, col_num):
        frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        tk_list = [tk.Label(frame, text=manip_str.title())]
        for k in self.params.keys():
            if k.startswith(manip_str):
                b = tk.Button(frame, text=k.title())
                b.config(fg='black', command=lambda manip=k, button=b: self.keythread.enable_manip(manip, button))
                tk_list.append(b)
        organise_pane(tk_list=tk_list, col_num=col_num)
        frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        self.tk_list.extend(tk_list)

    def log_text(self, text):
        self.logging_window.config(state='normal')
        self.logging_window.insert('end', text)
        self.logging_window.see("end")
        self.logging_window.config(state='disabled')


def organise_pane(tk_list, col_num, px=10, py=1):
    for row_num, b in enumerate(tk_list):
        b.grid(row=row_num, column=col_num, padx=px, pady=py)
