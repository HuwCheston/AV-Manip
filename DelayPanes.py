import numpy as np
import time
import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import PercentFormatter
import threading
import scipy.stats as stats


# TODO: all classes should have the option to delay audio and video separately
# TODO: set up all other delay panes to inherit shared methods from a single class

# TODO: fix resetting colours of buttons!

class DelayFromFile:
    def __init__(self, root: tk.Tk, params: dict, keythread, gui):
        self.params = params
        self.root = root
        self.gui = gui
        self.delay_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.keythread = keythread
        self.file = None  # Used as placeholder until file loaded in

        self.frame_1, self.delay_time_entry, self.label_1 = get_tk_entry(text='Time:', frame=self.delay_frame)
        self.delay_time_entry.insert(0, str(self.params['*delay time']))
        self.delay_time_entry.config(state='readonly')  # We don't need to modify the delay time directly
        self.frame_2, self.resample_entry, self.label_2 = get_tk_entry(text='Resample:', frame=self.delay_frame)
        self.resample_entry.insert(0, '1000')
        self.frame_3, self.baseline_entry, self.label_2 = get_tk_entry(text='Baseline:', frame=self.delay_frame)
        self.baseline_entry.insert(0, '50')

        # TODO: implement delay multiplier
        self.multiplier = tk.DoubleVar()
        self.slider = tk.Scale(
            self.delay_frame,
            from_=0,
            to=3.0,
            resolution=0.1,
            orient='horizontal',
            variable=self.multiplier
        )

        self.checkbutton_var = tk.IntVar()
        self.checkbutton = ttk.Checkbutton(self.delay_frame, text='Scale Delay?', var=self.checkbutton_var,
                                           command=self.checkbutton_func)
        self.checkbutton_func()

        self.open_file_button = tk.Button(self.delay_frame,
                                          command=self.open_file,
                                          text='Open File')
        self.start_delay_button = tk.Button(self.delay_frame,
                                            command=lambda:
                                            [self.keythread.enable_manip(manip='delayed',
                                                                         button=self.start_delay_button),
                                             threading.Thread(target=self.get_file_delay, daemon=True).start()],
                                            text='Start Delay')
        self.plot_prog_button = tk.Button(self.delay_frame, command=self.plot_delay_prog,
                                          text='Plot Progression')
        self.plot_hist_button = tk.Button(self.delay_frame, command=self.plot_delay_hist,
                                          text='Plot Distribution')

        self.tk_list = [
            tk.Label(self.delay_frame, text='Delay from File'),
            self.frame_2,
            self.checkbutton,
            self.frame_3,
            tk.Label(self.delay_frame, text='Multiplier'),
            self.slider,
            self.open_file_button,
            self.start_delay_button,
            self.plot_prog_button,
            self.plot_hist_button,
            self.frame_1,
        ]

    def open_file(self):
        filetypes = (
            ('CSV files', '*.csv'),
            ('Text files', '*.txt'),
            ('All files', '*.*'),
        )

        filename = tk.filedialog.askopenfile(
            title='Open a file',
            initialdir='./',
            filetypes=filetypes
        )
        self.file_to_array(filename)

    def scale_array(self, array):
        # Get the baseline and multiplier values given by the user
        baseline = try_get_entries([self.baseline_entry])[0]
        multiplier = self.multiplier.get()

        # Transpose the array to match the baseline
        func = lambda x: (x - array.min() + baseline)
        array = func(array)

        # Return an array scaled to the multiplier
        # TODO: Raise exception if new max value is now below the baseline!
        return np.interp(array, (array.min(), array.max()), (array.min(), array.max() * multiplier))

    def file_to_array(self, filename):
        # TODO: Improve this error catching process... will do for now. e.g. should make sure all elements are ints
        try:
            self.file = np.genfromtxt(filename, delimiter=',', dtype=int)
        except TypeError:  # This will trigger if the user cancels out of the file select window
            self.gui.log_text("\nCouldn't convert file to array!")
        else:
            if self.checkbutton_var.get() == 1:
                self.file = self.scale_array(array=self.file)
            self.gui.log_text(f"\nNew array loaded from file: length {self.file.size}")

    def get_file_delay(self):
        self.delay_time_entry.config(state='normal')
        self.resample_entry.config(state='readonly')
        resample = try_get_entries([self.resample_entry])[0]

        # TODO: catch TypeError if file not loaded yet
        while self.params['delayed']:
            for i in self.file:
                self.delay_time_entry.delete(0, 'end')
                self.delay_time_entry.insert(0, str(round(i)))
                set_delay_time(params=self.params, d_time=int(i))
                time.sleep(int(resample / 1000))

        self.delay_time_entry.delete(0, 'end')
        self.delay_time_entry.config(state='readonly')

    def plot_delay_prog(self):
        fig, ax = plt.subplots()
        ax.plot(range(len(self.file)), self.file)
        ax.set_ylabel('Delay (ms)')
        ax.set_xlabel('Delay Resample')
        ax.set_title("Delay from File: progression")
        pack_distribution_display(fig)

    def plot_delay_hist(self):
        fig, ax = plt.subplots()
        ax.hist(self.file, rwidth=0.9)
        ax.set_ylabel('Frequency')
        ax.set_xlabel('Delay (ms)')
        ax.set_title("Delay from File: distribution")
        pack_distribution_display(fig)

    def checkbutton_func(self):
        if self.checkbutton_var.get() == 0:
            self.slider.config(state='disabled', takefocus=0)
            self.baseline_entry['state'] = 'readonly'
        else:
            self.slider.config(state='normal', takefocus=0)
            self.baseline_entry['state'] = 'normal'


class FixedDelay:
    def __init__(self, root: tk.Tk, params: dict, keythread, gui):
        self.params = params
        self.root = root
        self.gui = gui
        self.delay_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.keythread = keythread

        self.frame_1, self.entry_1, self.label_1 = get_tk_entry(text='Time:', frame=self.delay_frame)
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

        self.frame_1, self.entry_1, self.label_1 = get_tk_entry(text='Low:', frame=self.delay_frame)
        self.frame_2, self.entry_2, self.label_2 = get_tk_entry(text='High:', frame=self.delay_frame)
        self.frame_3, self.entry_3, self.label_3 = get_tk_entry(text='Resample:', frame=self.delay_frame)
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
        self.delay_time_frame, self.delay_time_entry, self.delay_time_label = get_tk_entry(text='Delay Time:',
                                                                                           frame=self.delay_frame)
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


class IncrementalDelay:
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
        self.frame_1, self.start_entry, self.label_1 = get_tk_entry(text='Start:', frame=self.delay_frame)
        self.frame_2, self.finish_entry, self.label_2 = get_tk_entry(text='Finish:', frame=self.delay_frame)
        self.frame_3, self.length_entry, self.label_3 = get_tk_entry(text='Length:', frame=self.delay_frame)
        self.frame_4, self.resample_entry, self.label_4 = get_tk_entry(text='Resample:', frame=self.delay_frame)

        self.delay_time_frame, self.delay_time_entry, self.delay_time_label = get_tk_entry(text='Delay Time:',
                                                                                           frame=self.delay_frame)
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
                                             threading.Thread(target=self.get_incremental_delay,
                                                              daemon=True)
                                                      .start()],
                                            text='Start Delay')

        self.tk_list = [tk.Label(self.delay_frame, text='Incremental Delay'),
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
                             values=self.params['*incremental delay distributions'])
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
            # TODO: check this new maths works
            self.dist = np.interp(self.dist, (self.dist.min(), self.dist.max()), (start, end))

        else:  # Breaks out in case of incorrect input
            return

        # Save the distribution before rounding so we can use it later if we decide to plot the graph
        self.dist_unsmoothed = self.dist
        # Now we need to round the array as we can't use decimal ms values in Reaper/OpenCV
        self.dist = np.round(self.dist, 0).astype(np.int64)
        self.gui.log_text(f'\nNew array calculated!')

    def flip_delay_space(self):
        self.get_new_space()
        self.dist = np.flip(self.dist)
        self.dist_unsmoothed = np.flip(self.dist_unsmoothed)
        self.gui.log_text(f'\nArray flipped!')

    def plot_distribution(self, ):
        delay_length = try_get_entries([self.length_entry])[0]
        x = np.linspace(start=0, stop=delay_length, num=len(self.dist), endpoint=True)  # We always have to start at 0ms

        y = self.dist_unsmoothed
        y2 = self.dist

        fig, ax = plt.subplots()

        ax.set_xlabel('Delay Running Length (ms)')
        ax.set_ylabel('Delay Time (ms)')
        ax.set_xlim(0, delay_length)
        ax.set_ylim(self.dist.min(), self.dist.max())

        ax.plot(x, y, alpha=0.3, label='Interpolated Array')
        ax.scatter(x, y2, s=2, marker='.', alpha=1, label='Rounded Samples')

        ax2 = ax.twiny()
        ax2.set_xlim(0, len(self.dist))  # We always start with 0 cumulative resamples
        ax2.set_xlabel('Cumulative Resamples')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)

        pack_distribution_display(fig)

    def get_incremental_delay(self):
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
        self.gui.log_text(f'\nIncremental delay finished in {round(end - start, 2)} secs!')

        # If the delay has climbed all the way down to 0, we can turn off the delay as it's now unnecessary
        if self.params['*delay time'] <= 1:  # <=1 is used here as we may have substituted 1 for 0 when using np.log()
            self.keythread.reset_manips()
            self.delay_time_entry.delete(0, 'end')  # Only delete the text if we're also turning off the delay
        # Otherwise, we still need to keep the delay on.

        self.delay_time_entry.config(state='readonly')


def get_tk_entry(frame, text):
    frame = tk.Frame(frame)
    label = tk.Label(frame, text=text)
    entry = tk.Entry(frame, width=5)
    ms = tk.Label(frame, text='ms')
    label.grid(row=1, column=1)
    entry.grid(row=1, column=2)
    ms.grid(row=1, column=3)
    return frame, entry, label


def try_get_entries(entries: list):
    # TODO: fix error catching here...
    try:
        return tuple(int(val.get()) for val in entries)
    except ValueError:
        for entry in entries:
            entry.delete(0, 'end')
            entry.insert(0, 'NaN')
        return None


def pack_distribution_display(fig):
    newwindow = tk.Toplevel()
    canvas = FigureCanvasTkAgg(fig, master=newwindow)
    canvas.draw()
    canvas.get_tk_widget().pack()
    toolbar = NavigationToolbar2Tk(canvas, newwindow)
    toolbar.update()
    canvas.get_tk_widget().pack()


def set_delay_time(params, d_time: int, ):
    params['*delay time'] = d_time if 0 <= d_time < params['*max delay time'] else 0
