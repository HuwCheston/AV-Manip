import threading
import tkinter as tk

# TODO: experiment with using a Tkinter window, rather than a blank CV2 window - will enable buttons, rather than keys
class KeyThread:
    def __init__(self, params: dict, stop_event: threading.Event, global_barrier: threading.Barrier):
        self.name = 'Keypress Manager'
        self.stop_event = stop_event
        self.root = tk.Tk()
        self.root.title = self.name
        self.start_keymanager(global_barrier, params)

    def start_keymanager(self, global_barrier, params):
        self.wait(global_barrier)
        self.tk_setup(params)
        self.main_loop()

    def wait(self, global_barrier):
        print(f"{self.name} currently waiting. Waiting threads = {global_barrier.n_waiting + 1}\n")
        global_barrier.wait()

    def tk_setup(self, params):
        def set_delay():
            nonlocal params
            params['delay time'] = int(d_time.get())

        def manipulate(manip):
            nonlocal params
            params[manip] = True

        def reset():
            nonlocal params
            for p in params.keys():
                if isinstance(params[p], bool):
                    params[p] = False
            params['reset'] = True

        # TODO: add option to set variable delay time, to be read by CamThread and ReaThread

        canvas = tk.Canvas(self.root, width=500, height=400, bd=0, highlightthickness=0)
        canvas.pack()

        d_time = tk.Entry(canvas)
        d_time_get = tk.Button(canvas, text='Set', command=set_delay)
        b_list = [tk.Button(canvas, text=p.title(), command=lambda p=p: manipulate(p)) if p != 'reset'
                  else tk.Button(canvas, text=p.title(), command=reset) for p in params.keys()]
        b_list.append(tk.Button(canvas, text="Quit", command=self.exit_loop))
        d_time.pack()
        d_time_get.pack()
        for b in b_list:
            b.pack()

    def main_loop(self):
        self.root.mainloop()

    def exit_loop(self):
        self.stop_event.set()
        self.root.destroy()
