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
        self.root.wm_title("AV-Manip")
        self.root.iconbitmap("cms-logo.ico")

        # TODO: un-spaghetti this!
        info_frame = tk.Frame(self.root, padx=10, pady=1)
        info_frame.grid(row=1, column=1)
        img_label = tk.Label(info_frame)
        img_label.image = tk.PhotoImage(file="cms-logo.gif")
        img_label['image'] = img_label.image
        img_label.grid(row=1, column=1, sticky="n", padx=10, pady=10)
        version = tk.Label(info_frame, text='AV-Manip (v.0.1)')
        version.grid(row=2, column=1)
        # TODO: make this a hyperlink (see stack overflow)
        copyright = tk.Label(info_frame, text='© Huw Cheston, 2022')
        copyright.grid(row=3, column=1)
        participants = tk.Label(info_frame, text=f'Active participants: {str(self.params["*participants"])}')
        participants.grid(row=4, column=1)
        participants = tk.Label(info_frame, text=f'Camera FPS: {str(self.params["*fps"])}')
        participants.grid(row=5, column=1)

        command_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        command_tk_list = [tk.Label(command_tk_frame, text='Commands'),
                           tk.Button(command_tk_frame, text="Reset", command=self._reset_manips),
                           tk.Button(command_tk_frame, text="Quit", command=self.exit_loop)]
        self._organise_gui(tk_list=command_tk_list, col_num=2)
        command_tk_frame.grid(column=2, row=1, sticky="n", padx=10, pady=10)

        delay_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        delay_tk_list = self._populate_tk_list(manip_str='delay', frame=delay_tk_frame)
        d_time = tk.Entry(delay_tk_frame, width=5)
        d_time.insert(0, str(self.params['*delay time']))
        delay_tk_list.append(
            tk.Button(delay_tk_frame, text='Set Delay Time', command=lambda: self._set_delay_manip_time(d_time)))
        for (k, v) in self.params["*delay time presets"].items():
            delay_tk_list.append(tk.Button(delay_tk_frame, text=f'{k} - {str(v)} msec',
                                           command=lambda x=v: [d_time.delete(0, 'end'),
                                                                d_time.insert(0, str(x)),
                                                                self._set_delay_manip_time(d_time)]))
        delay_tk_list.append(d_time)
        # TODO: align this to the right of the entry textbox
        delay_tk_list.append(tk.Label(delay_tk_frame, text='msec'))
        self._organise_gui(tk_list=delay_tk_list, col_num=3)
        delay_tk_frame.grid(column=3, row=1, sticky="n", padx=10, pady=10)

        loop_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        loop_tk_list = self._populate_tk_list(manip_str='loop', frame=loop_tk_frame)
        self._organise_gui(tk_list=loop_tk_list, col_num=4)
        loop_tk_frame.grid(column=4, row=1, sticky="n", padx=10, pady=10)

        blank_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        blank_tk_list = self._populate_tk_list(manip_str='blank', frame=blank_tk_frame)
        self._organise_gui(tk_list=blank_tk_list, col_num=5)
        blank_tk_frame.grid(column=5, row=1, sticky="n", padx=10, pady=10)

        control_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        control_tk_list = self._populate_tk_list(manip_str='control', frame=control_tk_frame)
        self._organise_gui(tk_list=control_tk_list, col_num=6)
        control_tk_frame.grid(column=6, row=1, sticky="n", padx=10, pady=10)

        flip_tk_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        flip_tk_list = self._populate_tk_list(manip_str='flip', frame=flip_tk_frame)
        self._organise_gui(tk_list=flip_tk_list, col_num=7)
        flip_tk_frame.grid(column=7, row=1, sticky="n", padx=10, pady=10)

        biglist = [command_tk_list, delay_tk_list, loop_tk_list, blank_tk_list, control_tk_list, flip_tk_list]
        self.tk_list = [item for sublist in biglist for item in sublist]

    def _populate_tk_list(self, manip_str, frame):
        tk_list = [tk.Label(frame, text=manip_str.title())]
        for k in self.params.keys():
            if k.startswith(manip_str):
                b = tk.Button(frame, text=k.title())
                b.config(fg='black', command=lambda manip=k, button=b: self._set_manip(manip, button))
                tk_list.append(b)
        return tk_list

    def _organise_gui(self, tk_list, col_num):
        # TODO: Surely there's a better way to organise the GUI than this...
        for row_num, b in enumerate(tk_list):
            b.grid(row=row_num, column=col_num, padx=10, pady=1)

    def _set_delay_manip_time(self, d_time):
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

    def _set_manip(self, manip, button):
        self._reset_manips()
        self.params[manip] = True
        button.config(bg='green')

    def _reset_manips(self):
        # TODO: can this be replaced with an event? Will need to change ReaThread too
        self.params['*reset'] = True
        for button in self.tk_list:
            if isinstance(button, tk.Button):
                button.config(bg="SystemButtonFace")
        self.params['*reset lock'].acquire()
        for param in self.params.keys():
            if isinstance(self.params[param], bool):
                self.params[param] = False

    def main_loop(self):
        self.root.attributes('-topmost', 'true')
        self.root.mainloop()

    def exit_loop(self):
        self.stop_event.set()
        self.root.destroy()
