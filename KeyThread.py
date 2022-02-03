import threading
import tkinter as tk


class KeyThread:
    def __init__(self, params: dict, stop_event: threading.Event, global_barrier: threading.Barrier):
        self.name = 'Keypress Manager'
        self.stop_event = stop_event
        self.root = tk.Tk()
        self.root.title = self.name
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

    # TODO: refactor these into multiple functions (or class?)
    def tk_setup(self):
        command_tk_list = [tk.Label(text='Commands'),
                           tk.Button(self.root, text="Reset", command=self._reset_manips),
                           tk.Button(self.root, text="Quit", command=self.exit_loop)]
        self._organise_gui(tk_list=command_tk_list, col_num=2)

        delay_tk_list = []
        self._populate_tk_list(tk_list=delay_tk_list, manip_str='delay')
        d_time = tk.Entry(self.root)
        d_time.insert(0, str(self.params['*delay time']))
        delay_tk_list.append(d_time)
        delay_tk_list.append(
            tk.Button(self.root, text='Set Delay Time', command=lambda: self._set_delay_manip_time(d_time)))
        for (k, v) in self.params["*delay time presets"].items():
            delay_tk_list.append(tk.Button(self.root, text=f'{k} - {str(v)}',
                                           command=lambda x=v: [d_time.delete(0, 'end'),
                                                                d_time.insert(0, str(x)),
                                                                self._set_delay_manip_time(d_time)]))
        self._organise_gui(tk_list=delay_tk_list, col_num=3)

        loop_tk_list = []
        self._populate_tk_list(tk_list=loop_tk_list, manip_str='loop')
        self._organise_gui(tk_list=loop_tk_list, col_num=4)

        blank_tk_list = []
        self._populate_tk_list(tk_list=blank_tk_list, manip_str='blank')
        self._organise_gui(tk_list=blank_tk_list, col_num=5)

        control_tk_list = []
        self._populate_tk_list(tk_list=control_tk_list, manip_str='control')
        self._organise_gui(tk_list=control_tk_list, col_num=6)

        extra_manip_tk_list = []

        biglist = [command_tk_list, delay_tk_list, loop_tk_list, blank_tk_list, control_tk_list, extra_manip_tk_list]
        self.tk_list = [item for sublist in biglist for item in sublist]

    def _populate_tk_list(self, tk_list, manip_str):
        tk_list.append(tk.Label(text=manip_str.title()))
        for k in self.params.keys():
            if k.startswith(manip_str):
                b = tk.Button(self.root, text=k.title())
                b.config(fg='black', command=lambda manip=k, button=b: self._set_manip(manip, button))
                tk_list.append(b)

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

    def _organise_gui(self, tk_list, col_num):
        # TODO: Surely there's a better way to organise the GUI than this...
        for row_num, b in enumerate(tk_list):
            b.grid(row=row_num, column=col_num, padx=10, pady=1)

    def main_loop(self):
        self.root.attributes('-topmost', 'true')
        self.root.mainloop()

    def exit_loop(self):
        self.stop_event.set()
        self.root.destroy()
