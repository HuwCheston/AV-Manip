import threading
import tkinter as tk


class KeyThread:
    def __init__(self, params: dict, stop_event: threading.Event, global_barrier: threading.Barrier):
        self.name = 'Keypress Manager'
        self.stop_event = stop_event
        self.root = tk.Tk()
        self.params = params
        self.tk_list = []
        self.start_keymanager(global_barrier)

    def start_keymanager(self, global_barrier):
        self.wait(global_barrier)
        self.tk_setup()
        self.main_loop()

    def wait(self, global_barrier):
        print(f"{self.name} currently waiting. Waiting threads = {global_barrier.n_waiting + 1}\n")
        global_barrier.wait()

    def tk_setup(self):
        panes = [self.info_pane, self.command_pane, self.delay_pane, self.loop_pane, self.loop_pane,
                 self.blank_pane, self.control_pane, self.flip_pane]
        # TODO: disable having to suppress the inspection here...
        for num, pane in enumerate(panes):
            # noinspection PyArgumentList
            pane(col_num=num+1)

    def main_loop(self):
        self.root.attributes('-topmost', 'true')
        self.root.mainloop()

    def exit_loop(self):
        self.stop_event.set()
        self.root.destroy()

    def info_pane(self, col_num):
        # TODO: fix this and set it to use self.organise_gui
        info_frame = tk.Frame(self.root, padx=10, pady=1)
        info_frame.grid(row=1, column=col_num)
        img_label = tk.Label(info_frame)
        img_label.image = tk.PhotoImage(file="cms-logo.gif")
        img_label['image'] = img_label.image
        img_label.grid(row=1, column=col_num, sticky="n", padx=10, pady=10)

        labels = ['AV-Manip (v.0.1)',
                  '© Huw Cheston, 2022',
                  f'Active participants: {str(self.params["*participants"])}',
                  f'Camera FPS: {str(self.params["*fps"])}']
        for (num, label) in enumerate(labels):
            l = tk.Label(info_frame, text=label)
            l.grid(row=num, column=col_num)

    def command_pane(self, col_num):
        command_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        command_tk_list = [tk.Label(command_tk_frame, text='Commands'),
                           tk.Button(command_tk_frame, text="Reset", command=self.reset_manips),
                           tk.Button(command_tk_frame, text="Quit", command=self.exit_loop)]
        self.organise_gui(tk_list=command_tk_list, col_num=col_num)
        command_tk_frame.grid(column=2, row=1, sticky="n", padx=10, pady=10)

    def delay_pane(self, col_num):
        delay_params_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        delay_time_frame = tk.Frame(delay_params_tk_frame)
        d_time = tk.Entry(delay_time_frame, width=15)
        d_time.insert(0, str(self.params['*delay time']))
        msec = tk.Label(delay_time_frame, text='msec')
        delay_tk_list = [tk.Label(delay_params_tk_frame, text='Delay')]
        b = tk.Button(delay_params_tk_frame, text='Start Delay')
        b.config(fg='black', command=lambda manip='delayed', button=b: self.enable_manip(manip, button))
        delay_tk_list.append(b)
        delay_tk_list.append(tk.Button(delay_params_tk_frame, text='Set Delay Time', command=lambda: self.set_delay_time(d_time)))
        for (k, v) in self.params["*delay time presets"].items():
            delay_tk_list.append(tk.Button(delay_params_tk_frame, text=f'{k} - {str(v)} msec',
                                           command=lambda x=v: [d_time.delete(0, 'end'),
                                                                d_time.insert(0, str(x)),
                                                                self.set_delay_time(d_time)]))
        self.organise_gui(tk_list=delay_tk_list, col_num=1)
        delay_params_tk_frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
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
                b.config(fg='black', command=lambda manip=k, button=b: self.enable_manip(manip, button))
                tk_list.append(b)
        self.organise_gui(tk_list=tk_list, col_num=col_num)
        frame.grid(column=col_num, row=1, sticky="n", padx=10, pady=10)
        self.tk_list.extend(tk_list)

    def organise_gui(self, tk_list, col_num):
        for row_num, b in enumerate(tk_list):
            b.grid(row=row_num, column=col_num, padx=10, pady=1)

    def enable_manip(self, manip, button):
        self.reset_manips()
        self.params[manip] = True
        button.config(bg='green')

    def set_delay_time(self, d_time):
        try:
            d = int(d_time.get())
        except ValueError:
            d_time.delete(0, 'end')
            d_time.insert(0, 'Not a number')
        else:
            if 0 < d < self.params['*max delay time']:
                self.params['*delay time'] = d
            else:
                d_time.delete(0, 'end')
                d_time.insert(0, 'Out of bounds')

    def reset_manips(self):
        # TODO: can this be replaced with an event? Will need to change ReaThread too
        self.params['*reset'] = True
        for button in self.tk_list:
            if isinstance(button, tk.Button):
                button.config(bg="SystemButtonFace")
        self.params['*reset lock'].acquire()
        for param in self.params.keys():
            if isinstance(self.params[param], bool):
                self.params[param] = False
