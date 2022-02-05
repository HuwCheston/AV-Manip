import tkinter as tk
from tkinter import ttk
import webbrowser


class TkGui:
    def __init__(self, params, keythread):
        self.root = tk.Tk()
        self.root.attributes('-topmost', 'true')
        self.root.iconbitmap("cms-logo.ico")

        self.params = params
        self.keythread = keythread
        self.tk_list = []

    def tk_setup(self):
        panes = [
            self.info_pane,
            self.command_pane,
            self.delay_pane,
            self.loop_pane,
            self.loop_pane,
            self.blank_pane,
            self.control_pane,
            self.flip_pane
        ]

        # TODO: why does this need to be num+1?
        for num, pane in enumerate(panes):
            pane(col_num=num + 1)

    def info_pane(self, col_num):
        texts = [
            'AV-Manip (v.0.1)',
            '© Huw Cheston, 2022',
            f'Active participants: {str(self.params["*participants"])}',
            f'Camera FPS: {str(self.params["*fps"])}'
        ]

        info_frame = tk.Frame(self.root, padx=10, pady=1)
        img_label = tk.Label(info_frame, cursor="hand2")
        img_label.image = tk.PhotoImage(file="cms-logo.gif")
        img_label['image'] = img_label.image
        img_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://cms.mus.cam.ac.uk/"))

        labels = [img_label] + [tk.Label(info_frame, text=text) for text in texts]
        self.organise_pane(tk_list=labels, col_num=col_num, px=0, py=0)
        info_frame.grid(row=1, column=col_num)

    def command_pane(self, col_num):
        command_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        command_tk_list = [
            tk.Label(command_tk_frame, text='Commands'),
            tk.Button(command_tk_frame, text="Reset", command=self.keythread.reset_manips),
            tk.Button(command_tk_frame, text="Quit", command=self.keythread.exit_loop)
        ]
        self.organise_pane(tk_list=command_tk_list, col_num=col_num)
        command_tk_frame.grid(column=2, row=1, sticky="n", padx=10, pady=10)

    def delay_pane(self, col_num):
        delay_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        delay_time_frame = tk.Frame(delay_tk_frame)
        d_time = tk.Entry(delay_time_frame, width=15)
        d_time.insert(0, str(self.params['*delay time']))
        msec = tk.Label(delay_time_frame, text='msec')
        delay_tk_list = [tk.Label(delay_tk_frame, text='Delay')]
        b = tk.Button(delay_tk_frame, text='Start Delay')
        b.config(fg='black', command=lambda manip='delayed', button=b: self.keythread.enable_manip(manip, button))
        delay_tk_list.append(b)
        delay_tk_list.append(tk.Button(delay_tk_frame, text='Set Delay Time',
                                       command=lambda: self.keythread.set_delay_time(d_time)))

        preset_list = [v for (k, v) in self.params["*delay time presets"].items()]
        combobox = ttk.Combobox(delay_tk_frame,
                                values=[f'{k} - {v} msec' for (k, v) in self.params["*delay time presets"].items()],
                                state='readonly')
        combobox.set('Delay Time Presets')
        combobox.bind("<<ComboboxSelected>>",
                      lambda e: [d_time.delete(0, 'end'),
                                 d_time.insert(0, str(preset_list[combobox.current()])),
                                 self.keythread.set_delay_time(d_time)])
        delay_tk_list.append(combobox)
        self.organise_pane(tk_list=delay_tk_list, col_num=1)
        delay_tk_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        delay_time_frame.grid(column=1, row=10, sticky="n", padx=10, pady=10)
        d_time.grid(row=1, column=1, sticky='n')
        msec.grid(row=1, column=2, sticky='n')
        self.tk_list.extend(delay_tk_list)

    def loop_pane(self, col_num):
        manip_str = 'loop'
        self.populate_tk_list(manip_str, col_num=col_num)

    def blank_pane(self, col_num):
        manip_str = 'blank'
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
        self.organise_pane(tk_list=tk_list, col_num=col_num)
        frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        self.tk_list.extend(tk_list)

    def organise_pane(self, tk_list, col_num, px=10, py=1):
        for row_num, b in enumerate(tk_list):
            b.grid(row=row_num, column=col_num, padx=px, pady=py)
