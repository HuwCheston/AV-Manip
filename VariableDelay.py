import random
import numpy as np
import time
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import threading
import scipy.stats as stats


class VariableDelay:
    def __init__(self, params, root: tk.Tk):
        self.params = params
        self.root = root
        self.variable_delay_frame = tk.Frame(self.root, borderwidth=2, relief="groove")

        self.dist = None
        self.delay_value = float
        self.delay_time = float

        self.mu_frame, self.mu_entry = self.get_tk_entry(text='Mu')
        self.sigma_frame, self.sigma_entry = self.get_tk_entry(text='Sigma')
        self.low_timer_frame, self.low_timer = self.get_tk_scale(text='Lower')
        self.high_timer_frame, self.high_timer = self.get_tk_scale(text='Upper')

        self.get_new_dist = tk.Button(self.variable_delay_frame, command=self.get_new_distribution,
                                      text='Get Distribution')
        self.plot_dist_button = tk.Button(self.variable_delay_frame, command=self.plot_distribution,
                                          text='Plot Distribution')

        self.tk_list = [tk.Label(self.variable_delay_frame, text='Variable Delay'),
                        self.mu_frame,
                        self.sigma_frame,
                        self.low_timer_frame,
                        self.high_timer_frame,
                        self.get_new_dist,
                        self.plot_dist_button]

    def get_tk_entry(self, text):
        frame = tk.Frame(self.variable_delay_frame)
        label = tk.Label(frame, text=text + ':')
        entry = tk.Entry(frame, width=5)
        ms = tk.Label(frame, text='ms')
        label.grid(row=1, column=1)
        entry.grid(row=1, column=2)
        ms.grid(row=1, column=3)
        return frame, entry

    def get_tk_scale(self, text):
        frame = tk.Frame(self.variable_delay_frame)
        label = tk.Label(frame,)
        # TODO: Replace scale boundaries in user params
        scale = tk.Scale(frame, from_=0, to=1000, orient='horizontal', label=text + ' boundary:')
        label.grid(row=1, column=1)
        scale.grid(row=1, column=2)
        return frame, scale

    def get_new_distribution(self, ):
        try:
            mu, sigma = int(self.mu_entry.get()), int(self.sigma_entry.get())
        except ValueError:
            for entry in [self.mu_entry, self.sigma_entry]:
                entry.delete(0, 'end')
                entry.insert(0, 'NaN')
        else:
            self.dist = np.random.normal(mu, sigma, 1000)
            self.delay_value = np.random.choice(self.dist)

    def plot_distribution(self,):
        newwindow = tk.Toplevel()
        fig, ax = plt.subplots()
        x_bin, y_bin = self.get_hist(ax)
        ax.annotate(text=f'{round(x_bin, 2)}ms', xy=(x_bin, y_bin), xytext=(x_bin, y_bin + 0.005),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3"))
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
