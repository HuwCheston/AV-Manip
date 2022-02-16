import numpy as np
import time
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import threading
import scipy.stats as stats


class VariableDelay:
    def __init__(self, params, root: tk.Tk, keythread):
        self.params = params
        self.root = root
        self.variable_delay_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
        self.keythread = keythread

        self.dist = None
        self.delay_value = float
        self.delay_time = float
        self.distribution_type = tk.IntVar(self.variable_delay_frame, 0)

        self.mu_frame, self.entry_1, self.label_1 = self.get_tk_entry(text='Low:')
        self.sigma_frame, self.entry_2, self.label_2 = self.get_tk_entry(text='High:')
        self.buttons_frame, self.buttons = self.get_tk_buttons()

        self.get_new_dist = tk.Button(self.variable_delay_frame, command=self.get_new_distribution,
                                      text='Get Distribution')
        self.plot_dist_button = tk.Button(self.variable_delay_frame, command=self.plot_distribution,
                                          text='Plot Distribution')
        self.start_delay_button = tk.Button(self.variable_delay_frame,
                                            command=lambda:
                                            [self.keythread.enable_manip(manip='delayed',
                                                                         button=self.start_delay_button),
                                             threading.Thread(target=self.get_random_delay, daemon=True).start()],
                                            text='Start Delay')
        self.delay_time_frame, self.delay_time_entry, self.delay_time_label = self.get_tk_entry(text='Delay Time:')
        self.delay_time_entry.config(state='readonly')

        self.tk_list = [tk.Label(self.variable_delay_frame, text='Variable Delay'),
                        self.buttons_frame,
                        self.mu_frame,
                        self.sigma_frame,
                        self.get_new_dist,
                        self.plot_dist_button,
                        self.start_delay_button,
                        self.delay_time_frame,
                        ]

    def get_tk_buttons(self):
        # TODO: convert this into a combobox
        # TODO: add more distributions
        # TODO: check Poisson distribution is working
        values = {"Uniform": 0,
                  "Gaussian": 1,
                  "Poisson": 2}
        texts = [['Low:', 'High:'], ['Mu:', 'Sigma:'], ['Expected:', 'N/A']]
        frame = tk.Frame(self.variable_delay_frame)

        buttons = [tk.Radiobutton(frame, text=t, variable=self.distribution_type, value=val,
                                  command=lambda: [self.label_1.configure(text=texts[self.distribution_type.get()][0]),
                                                   self.label_2.configure(text=texts[self.distribution_type.get()][1])])
                   for (t, val) in values.items()]
        for (num, button) in enumerate(buttons):
            button.grid(row=1, column=num)

        lab = tk.Label(frame, text='dist.')
        lab.grid(row=1, column=len(buttons)+1)
        return frame, buttons

    def get_tk_entry(self, text):
        frame = tk.Frame(self.variable_delay_frame)
        label = tk.Label(frame, text=text)
        entry = tk.Entry(frame, width=5)
        ms = tk.Label(frame, text='ms')
        label.grid(row=1, column=1)
        entry.grid(row=1, column=2)
        ms.grid(row=1, column=3)
        return frame, entry, label

    def get_new_distribution(self, ):
        try:
            val1, val2 = int(self.entry_1.get()), int(self.entry_2.get())
        except ValueError:
            for entry in [self.entry_1, self.entry_2]:
                entry.delete(0, 'end')
                entry.insert(0, 'NaN')
        # TODO: set shape of distribution as parameter
        else:
            if self.distribution_type.get() == 0:
                self.dist = np.random.uniform(val1, val2, 1000)
            elif self.distribution_type.get() == 1:
                self.dist = np.random.normal(val1, val2, 1000)
            # TODO: Check poisson implementation
            elif self.distribution_type.get() == 2:
                self.dist = np.random.poisson(val1, 1000)
            self.delay_value = np.random.choice(self.dist)

    def plot_distribution(self,):
        newwindow = tk.Toplevel()
        fig, ax = plt.subplots()
        x_bin, y_bin = self.get_hist(ax)
        ax.annotate(text=f'{round(x_bin, 2)}ms', xy=(x_bin, y_bin), xytext=(x_bin, y_bin + 0.005),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3"))
        if self.distribution_type.get() != 0:
            x, y = self.get_gauss_curve()
            ax.plot(x, y)
        self.pack_distribution_display(fig, newwindow)

    def get_hist(self, ax):
        ybins, xbins, _ = ax.hist(self.dist, bins=30, density=True)
        ind_bin = np.where(xbins >= self.delay_value)[0]
        x_bin = xbins[ind_bin[0] - 1] / 2. + xbins[ind_bin[0]] / 2.
        y_bin = ybins[ind_bin[0] - 1]
        return x_bin, y_bin

    def get_gauss_curve(self):
        mean, std = stats.norm.fit(self.dist)
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        y = stats.norm.pdf(x, mean, std)
        return x, y

    def pack_distribution_display(self, fig, newwindow):
        canvas = FigureCanvasTkAgg(fig, master=newwindow)
        canvas.draw()
        canvas.get_tk_widget().pack()
        toolbar = NavigationToolbar2Tk(canvas, newwindow)
        toolbar.update()
        canvas.get_tk_widget().pack()

    def get_random_delay(self):
        self.delay_time_entry.config(state='normal')
        while self.params['delayed']:
            self.delay_value = abs(np.random.choice(self.dist))
            self.delay_time_entry.delete(0, 'end')
            self.delay_time_entry.insert(0, str(round(self.delay_value)))
            self.keythread.set_delay_time(d_time=self.delay_time_entry)
            time.sleep(self.delay_value/1000)
        self.delay_time_entry.delete(0, 'end')
        self.delay_time_entry.config(state='readonly')
