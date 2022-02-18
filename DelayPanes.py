import numpy as np
import time
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.ticker import PercentFormatter
import threading
import scipy.stats as stats

# TODO: all classes should have the option to delay audio and video seperately
# TODO: set up all other delay panes to inherit shared methods from a single class


class FixedDelay:
    def __init__(self, root: tk.Tk, params: dict, keythread, gui):

        self.params = params
        self.root = root
        self.gui = gui
        self.delay_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.keythread = keythread

        self.frame_1, self.entry_1, self.label_1 = get_tk_entry(text='Time:', parent_frame=self.delay_frame)
        self.entry_1.insert(0, str(self.params['*delay time']))

        self.combo = self.get_tk_combo()

        self.set_delay_button = tk.Button(self.delay_frame,
                                          command=lambda: set_delay_time(d_time=try_get_entries([self.entry_1])[0],
                                                                         params=self.params),
                                          text='Set Delay')
        self.start_delay_button = tk.Button(self.delay_frame,
                                            command=lambda:
                                            [self.keythread.enable_manip(manip='delayed',
                                                                         button=self.start_delay_button)],
                                            text='Start Delay')

        self.tk_list = [tk.Label(self.delay_frame, text='Fixed Delay'),
                        self.frame_1,
                        self.combo,
                        self.set_delay_button,
                        self.start_delay_button,
                        ]

    def get_tk_combo(self):
        preset_list = [v for (k, v) in self.params["*delay time presets"].items()]
        combo = ttk.Combobox(self.delay_frame, state='readonly',
                             values=[f'{k} - {v} msec' for (k, v) in self.params["*delay time presets"].items()])
        combo.set('Delay Time Presets')
        combo.bind("<<ComboboxSelected>>",
                   lambda e: [self.entry_1.delete(0, 'end'),
                              self.entry_1.insert(0, str(preset_list[combo.current()])),
                              set_delay_time(d_time=try_get_entries([self.entry_1])[0], params=self.params)])
        return combo


class VariableDelay:
    def __init__(self, params, root: tk.Tk, keythread):
        self.params = params
        self.root = root
        self.delay_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.keythread = keythread

        self.dist = None
        self.delay_value = float
        self.delay_time = float

        self.frame_1, self.entry_1, self.label_1 = get_tk_entry(text='Low:', parent_frame=self.delay_frame)
        self.frame_2, self.entry_2, self.label_2 = get_tk_entry(text='High:', parent_frame=self.delay_frame)
        self.frame_3, self.entry_3, self.label_3 = get_tk_entry(text='Resample:', parent_frame=self.delay_frame)
        self.checkbutton = ttk.Checkbutton(self.delay_frame, text='Use as Resample Rate',
                                           command=self.checkbutton_func)

        self.combo = self.get_tk_combo()

        self.get_new_dist = tk.Button(self.delay_frame, command=self.get_new_distribution,
                                      text='Get Distribution')
        self.plot_dist_button = tk.Button(self.delay_frame, command=self.plot_distribution,
                                          text='Plot Distribution')
        self.start_delay_button = tk.Button(self.delay_frame,
                                            command=lambda:
                                            [self.keythread.enable_manip(manip='delayed',
                                                                         button=self.start_delay_button),
                                             threading.Thread(target=self.get_random_delay, daemon=True).start()],
                                            text='Start Delay')
        self.delay_time_frame, self.delay_time_entry, self.delay_time_label = get_tk_entry(text='Delay Time:', parent_frame=self.delay_frame)
        self.delay_time_entry.config(state='readonly')

        self.tk_list = [tk.Label(self.delay_frame, text='Variable Delay'),
                        self.combo,
                        self.frame_1,
                        self.frame_2,
                        self.frame_3,
                        self.get_new_dist,
                        self.plot_dist_button,
                        self.start_delay_button,
                        self.delay_time_frame,
                        self.checkbutton
                        ]

    def checkbutton_func(self):
        self.entry_3['state'] = 'readonly' if self.entry_3['state'] == 'normal' else 'normal'

    def get_tk_combo(self):
        # TODO: check Poisson distribution is working
        combo = ttk.Combobox(self.delay_frame, state='readonly',
                             values=[k for (k, _) in self.params['*var delay distributions'].items()])
        combo.set('Delay Distribution')
        combo.bind('<<ComboboxSelected>>', lambda e: [self.label_1
                   .configure(text=self.params['*var delay distributions'][combo.get()]['text'][0]),
                                                      self.label_2
                   .configure(text=self.params['*var delay distributions'][combo.get()]['text'][1])])
        return combo

    def get_new_distribution(self, ):
        entries = [self.entry_1, self.entry_2]
        val1, val2 = try_get_entries(entries)
        func = eval(self.params['*var delay distributions'][self.combo.get()]['function'])
        self.dist = func(val1, val2, self.params['*var delay samples'])
        self.delay_value = np.random.choice(self.dist)

    def plot_distribution(self, ):
        fig, ax = plt.subplots()

        if self.combo.get() == 'Gaussian':
            ax.hist(self.dist, bins=30, density=True, weights=np.ones(len(self.dist)) / len(self.dist))
            ax.yaxis.set_major_formatter(PercentFormatter(1))
            x, y = self.get_gauss_curve()
            ax.plot(x, y)

        else:
            ax.hist(self.dist, bins=30, density=True)

        ax.set_xlabel('Delay Time (ms)')
        ax.set_ylabel('Sample Probability')
        ax.set_title(f'Variable Delay: {self.combo.get()} distribution')

        pack_distribution_display(fig)

    def get_gauss_curve(self):
        mean, std = stats.norm.fit(self.dist)
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        y = stats.norm.pdf(x, mean, std)
        return x, y

    def get_random_delay(self):
        # TODO: check the readonly/normal state behaviour here
        # TODO: fix the occasional valueerror arising here
        self.delay_time_entry.config(state='normal')
        self.entry_3.config(state='readonly')
        while self.params['delayed']:
            self.delay_value = abs(np.random.choice(self.dist))
            self.delay_time_entry.delete(0, 'end')
            self.delay_time_entry.insert(0, str(round(self.delay_value)))
            set_delay_time(params=self.params, d_time=self.delay_value)
            time.sleep(int(self.delay_time_entry.get()) / 1000 if 'selected' in self.checkbutton.state() else int(
                self.entry_3.get()) / 1000)
        self.delay_time_entry.delete(0, 'end')
        self.delay_time_entry.config(state='readonly')


class MovingDelay:
    def __init__(self, params, root: tk.Tk, keythread, gui):
        self.params = params
        self.root = root
        self.gui = gui
        self.delay_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.keythread = keythread

        self.dist = None
        self.dist_unsmoothed = None
        self.delay_value = float

        self.combo = self.get_tk_combo()
        self.frame_1, self.start_entry, self.label_1 = get_tk_entry(text='Start:', parent_frame=self.delay_frame)
        self.frame_2, self.finish_entry, self.label_2 = get_tk_entry(text='Finish:', parent_frame=self.delay_frame)
        self.frame_3, self.length_entry, self.label_3 = get_tk_entry(text='Length:', parent_frame=self.delay_frame)
        self.frame_4, self.resample_entry, self.label_4 = get_tk_entry(text='Resample:', parent_frame=self.delay_frame)

        self.delay_time_frame, self.delay_time_entry, self.delay_time_label = get_tk_entry(text='Delay Time:',
                                                                                           parent_frame=self.delay_frame)
        self.delay_time_entry.config(state='readonly')

        self.get_new_space_button = tk.Button(self.delay_frame, command=self.get_new_space,
                                              text='Get Space')
        self.flip_delay_button = tk.Button(self.delay_frame, command=self.flip_delay_space,
                                           text='Flip Delay')
        self.plot_dist_button = tk.Button(self.delay_frame, command=self.plot_distribution,
                                          text='Plot Space')
        self.start_delay_button = tk.Button(self.delay_frame,
                                            command=lambda:
                                            [self.keythread.enable_manip(manip='delayed',
                                                                         button=self.start_delay_button),
                                             threading.Thread(target=self.get_moving_delay,
                                                              daemon=True)
                                                      .start()],
                                            text='Start Delay')

        self.tk_list = [tk.Label(self.delay_frame, text='Moving Delay'),
                        self.combo,
                        self.frame_1,
                        self.frame_2,
                        self.frame_3,
                        self.frame_4,
                        self.get_new_space_button,
                        self.flip_delay_button,
                        self.plot_dist_button,
                        self.start_delay_button,
                        self.delay_time_frame,
                        ]

    def get_tk_combo(self):
        combo = ttk.Combobox(self.delay_frame, state='readonly',
                             values=self.params['*moving delay distributions'])
        combo.set('Delay Space')
        return combo

    def get_new_space(self):
        entries = [self.start_entry, self.finish_entry, self.length_entry, self.resample_entry]
        (start, end, length, resample) = try_get_entries(entries)

        if str(self.combo.get()) == 'Linear':
            self.dist = np.linspace(start=start,
                                    stop=end,
                                    num=int(length / resample),
                                    endpoint=True)

        elif str(self.combo.get()) == 'Exponential':
            self.dist = np.logspace(start=np.log(start) if start != 0 else 0,  # We can't have log 0, so replace with 0
                                    stop=np.log(end),
                                    num=int(length / resample),
                                    endpoint=True,
                                    base=np.exp(1))

        elif str(self.combo.get()) == 'Natural Log':
            # (I'm sure there are better ways of doing this: but, man, am I bad at math.)
            # Get a natural log array by computing the log of a linear interpolation
            self.dist = np.log(np.linspace(start=1 if start <= 0 else start,  # We can't have log 0, so replace with 1
                                           stop=end,
                                           num=int(length / resample),
                                           endpoint=True))

            # Scale the array back to match.
            self.dist *= end / self.dist.max()

        else:  # Breaks out in case of incorrect input
            return

        # Save the distribution before rounding so we can use it later when plotting
        self.dist_unsmoothed = self.dist
        # Now we need to round the array as we can't use decimal ms values in Reaper/OpenCV
        self.dist = np.round(self.dist, 0).astype(np.int64)
        self.gui.log_text(f'\nNew array calculated!')

    def flip_delay_space(self):
        self.get_new_space()
        self.dist = np.flip(self.dist)
        self.gui.log_text(f'\nArray flipped!')

    def plot_distribution(self, ):
        x = np.linspace(start=self.dist.min(), stop=self.dist.max(), num=len(self.dist), endpoint=True)
        y = self.dist_unsmoothed
        y2 = self.dist

        fig, ax = plt.subplots()
        ax.set_xlabel('Delay Run Length (ms)')
        ax.set_ylabel('Delay Time (ms)')
        ax.set_title(f'Moving Delay: {self.combo.get()} space')
        ax.plot(x, y, alpha=0.3)
        ax.scatter(x, y2, s=2, marker='.', alpha=1)

        # TODO: align the ticks here!
        ax2 = ax.twiny()
        ax2.set_xlim(0, len(self.dist))
        ax2.set_xlabel('Cumulative Resamples')
        plt.legend(['Curve', 'Samples'])

        pack_distribution_display(fig)

    def get_moving_delay(self):
        self.delay_time_entry.config(state='normal')
        resample = try_get_entries([self.resample_entry])[0] / 1000
        start = time.time()

        # Iterate through our delay array
        for num in self.dist:
            self.delay_time_entry.delete(0, 'end')
            self.delay_time_entry.insert(0, num)
            set_delay_time(params=self.params, d_time=int(num))

            # If we're still delaying, wait for the resample rate
            if self.params['delayed']:
                time.sleep(resample)
            else:
                break

        # Log completion time in the gui console (to check against length inputted by user)
        end = time.time()
        self.gui.log_text(f'\nMoving delay finished in {round(end - start, 2)} secs!')

        # If the delay has climbed all the way down to 0, we can turn off the delay as it's now unnecessary
        if self.params['*delay time'] <= 1:  # 1 used, as we may have substituted 1 for 0 when using np.log()
            self.keythread.reset_manips()
            self.delay_time_entry.delete(0, 'end')  # Only delete the text if we're also turning off the delay

        self.delay_time_entry.config(state='readonly')


def get_tk_entry(parent_frame, text):
    frame = tk.Frame(parent_frame)
    label = tk.Label(frame, text=text)
    entry = tk.Entry(frame, width=5)
    ms = tk.Label(frame, text='ms')
    label.grid(row=1, column=1)
    entry.grid(row=1, column=2)
    ms.grid(row=1, column=3)
    return frame, entry, label


def try_get_entries(entries: list):
    try:
        ints = (int(val.get()) for val in entries)
    except ValueError:
        for entry in entries:
            entry.delete(0, 'end')
            entry.insert(0, 'NaN')
        return
    else:
        return tuple(ints)


def pack_distribution_display(fig):
    newwindow = tk.Toplevel()
    canvas = FigureCanvasTkAgg(fig, master=newwindow)
    canvas.draw()
    canvas.get_tk_widget().pack()
    toolbar = NavigationToolbar2Tk(canvas, newwindow)
    toolbar.update()
    canvas.get_tk_widget().pack()


def set_delay_time(params, d_time: int,):
    params['*delay time'] = d_time if 0 <= d_time < params['*max delay time'] else 0
