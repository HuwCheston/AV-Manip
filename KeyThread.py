import threading
import tkinter as tk


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

    # TODO: refactor these into multiple functions (or class?)
    def tk_setup(self, params):
        def set_delay():
            try:
                d = int(d_time.get())
            except ValueError:
                d_time.delete(0, 'end')
                d_time.insert(0, 'Not a number')
            else:
                if 0 < d < params['*max delay time']:
                    params['*delay time'] = d
                else:
                    d_time.delete(0, 'end')
                    d_time.insert(0, 'Out of bounds')

        def manipulate(manip, button):
            reset()
            params[manip] = True
            button.config(bg='green')

        def reset():
            # TODO: can this be replaced with an event? Will need to change ReaThread too
            params['*reset'] = True
            for button in tk_list:
                if isinstance(button, tk.Button):
                    button.config(bg="SystemButtonFace")
            params['*reset lock'].acquire()
            for param in params.keys():
                if isinstance(params[param], bool):
                    params[param] = False

        tk_list = []
        canvas = tk.Canvas(self.root, width=500, height=400, bd=0, highlightthickness=0)
        tk_list.append(canvas)

        d_time = tk.Entry(canvas)
        d_time.insert(0, str(params['*delay time']))
        tk_list.append(d_time)
        tk_list.append(tk.Button(canvas, text='Set Delay Time', command=set_delay))

        for p in params.keys():
            if not p.startswith('*'):
                b = tk.Button(canvas, text=p.title())
                b.config(fg='black', command=lambda manip=p, button=b: manipulate(manip, button))
                tk_list.append(b)
            elif p == '*reset':
                tk_list.append(tk.Button(canvas, text=p[1:].title(), command=reset))
            elif p == '*quit':
                tk_list.append(tk.Button(canvas, text=p[1:].title(), command=self.exit_loop))
            elif p == '*delay time presets':
                for (k, v) in params[p].items():
                    tk_list.append(
                        tk.Button(canvas, text=f'{k} - {str(v)}', command=lambda x=v: [d_time.delete(0, 'end'),
                                                                                       d_time.insert(0, str(x)),
                                                                                       set_delay()]))

        # TODO: Surely there's a better way to organise the GUI than this...
        for b in tk_list:
            b.pack()

    def main_loop(self):
        self.root.mainloop()

    def exit_loop(self):
        self.stop_event.set()
        self.root.destroy()
