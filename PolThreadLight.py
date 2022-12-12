import asyncio
import os
import tkinter as tk
from tkinter import scrolledtext, filedialog
import threading
from datetime import datetime, timezone
from bleak import BleakClient
import pandas as pd
from typing import Callable
import struct
import math
import pickle

"""Polar UUIDs"""
# This dictionary contains the UUIDs required to
UUID = {
    "PMD_Service": "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8",  # Not used here
    "PMD_Control": "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8",  # Bytes sent to this point to start streams
    "PMD_Data": "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8",  # PPG/timestamp data received from this point
    "FW": "00002A26-0000-1000-8000-00805f9b34fb",   # Not used (good for debugging)
    "HR_UUID": "00002A37-0000-1000-8000-00805F9B34FB",  # HR data received from this point
}

"""GATT Chars"""
# These bytearrays are sent to the Polar unit at the PMD_Control point
REQUEST_SETTINGS = bytearray(       # Gets measurement settings for PPG stream
    [0x01, 0x01]
)
SDK_MODE = bytearray(
    [0x02, 0x09]
)
STOP_SDK = bytearray(
    [0x03, 0x09]
)
START_PPG = bytearray(      # Open PPG stream   0xb0 = 176Hz
    [0x02, 0x01, 0x00, 0x01, 0xb0, 0x00, 0x01, 0x01, 0x16, 0x00, 0x04, 0x01, 0x04]
)
START_PPI = bytearray(      # Open PPI stream
    [0x02, 0x03]
)
START_ACC = bytearray(      # Open ACC stream
    [0x02, 0x02, 0x00, 0x01, 0x34, 0x00, 0x01, 0x01, 0x10, 0x00, 0x02, 0x01, 0x08, 0x00, 0x04, 0x01, 0x03]
)

"""Timestamp constants"""
# According to the Polar technical documentation, the epoch time in polar sensors is 2000-01-01T00:00:00Z,
# not the standard Unix 1970-01-01T00:00:00Z, so we need to offset this difference.
DIV = 1000000000
OFFSET = 946684800000000000 / DIV
TIME_FMT = '%Y-%m-%d %H:%M:%S.%f'   # strftime format
TIME_FMT_SAVE = '%Y-%m-%d_%H-%M-%S'


class PolThread:
    """Receives biometric data from a single Polar Verity Sense unit over Bluetooth LE"""
    def __init__(
            self, address: str, is_recording: bool, logger: Callable
    ):
        self.running = asyncio.Event()
        self.output_folder: str = os.getcwd()
        self.address = address[0]
        self.desc = address[1] if isinstance(address[1], str) else self.address
        self.is_recording: bool = is_recording
        self.logger = logger

        # Results are appended into the corresponding lists here
        self.results = {s: [] for s in address[2]}
        self.raw_data = {s: [] for s in address[2]}
        # Used to log if its the first time a stream has reported data
        self.is_firstrun = {k: True for k in self.results.keys()}

        self.timer = datetime.now()
        self.client = BleakClient(self.address)
        threading.Thread(target=asyncio.run, args=(self._init_polar(),)).start()

    async def _init_polar(
            self
    ) -> None:
        """
        Send bytes to PMD Control to start data streams and keep them alive until the GUI is closed
        """
        try:
            await self.client.connect()
        # If no device was found, close PolThread and log the error in the GUI
        except Exception as e:
            self.logger(f'{self.desc}: {e}')
        else:
            # Open all necessary streams
            await self._open_streams()
            # Wait for stop event, set with call of polar.quit_polar() in KeyThread
            await self.running.wait()
            # Close all opened streams
            await asyncio.gather(*self._close_streams())
        finally:
            # Disconnect from client
            await self.client.disconnect()

    async def _open_streams(
            self
    ) -> None:
        """
        Gathers functions to open Polar streams. Doesn't run concurrently, as need to wait when SDK activated
        """
        # Report initialisation
        await self.client.start_notify(UUID['PMD_Control'], self._report_init)
        # Gathering HR
        if 'hr' in self.results:
            # Receive HR data
            await self.client.start_notify(UUID['HR_UUID'], self._format_hr)
        # Gathering PPG
        if 'ppg' in self.results:
            # Start SDK mode
            await self.client.write_gatt_char(UUID['PMD_Control'], SDK_MODE, response=True)
            await asyncio.sleep(5)
            # Open PPG stream
            await self.client.write_gatt_char(UUID['PMD_Control'], START_PPG, response=True)
            # Gather data from PPI stream
            await self.client.start_notify(UUID['PMD_Data'], self._format_ppg)
        # Gathering PPI
        if 'ppi' in self.results:
            # Open PPI stream
            await self.client.write_gatt_char(UUID['PMD_Control'], START_PPI, response=True)
            # Gather data from PPI stream
            await self.client.start_notify(UUID['PMD_Data'], self._format_ppi)

    def _close_streams(
            self
    ) -> list[Callable]:
        """
        Gathers functions to close open Polar streams
        """
        tasks = []
        if 'hr' in self.results:
            tasks.append(self.client.stop_notify(UUID['HR_UUID']))  # Stop HR data
        if 'ppi' in self.results:
            tasks.append(self.client.stop_notify(UUID['PMD_Data']))  # Stop PPG or PPI data
        if 'ppg' in self.results:
            tasks.append(self.client.stop_notify(UUID['PMD_Data']))
            tasks.append(self.client.write_gatt_char(UUID['PMD_Control'], STOP_SDK))
        tasks.append(self.client.stop_notify(UUID['PMD_Control']))  # Stop PMD Control
        return tasks

    def _report_init(
            self, _, data: bytearray
    ) -> None:
        """
        Report once correct response reported from device
        """
        # TODO: fix this!
        if data == bytearray(b'\xf0\x01\x01\x00\x00\x00\x01\x87\x00\x01\x01\x16\x00\x04\x01\x04'):  # success response
            self.logger(f'{self.desc}: connected')
        if data == bytearray([0xF0, 0x02, 0x09, 0x00, 0x00]):
            self.logger(f'{self.desc}: SDK mode enabled')

    def _format_ppi(
            self, _, data: bytearray
    ) -> None:
        """
        Formats incoming PPI stream, combines with OS timestamp and appends to required list
        """
        # Append raw data plus timestamp
        if self.is_recording:
            self.raw_data['ppi'].append((datetime.now(tz=timezone.utc).strftime(TIME_FMT), data))
        type1, _, type2 = struct.unpack("<BqB", data[0:10])
        # If data is from PPI stream
        if type1 == 3:
            num = math.floor((len(data) - 8) / 6)
            for x in range(num):
                start = 10 + x * 6
                sample = data[start: start + 6]
                hr, ppi, err, flags = struct.unpack("<BHHB", sample)
                sample = {
                    'address': self.address,
                    'desc': self.desc,
                    'timestamp': datetime.now(tz=timezone.utc).strftime(TIME_FMT),
                    'heart_rate': hr,
                    'ppi_ms': ppi,
                    'error_estimate': err,
                    'flags': flags
                }
                self._append_results(stream='ppi', data=sample)

    @staticmethod
    def _convert_to_timestamp(
            data: bytearray, start: int, end: int
    ) -> datetime:
        """
        Converts bytearray to timestamp
        """
        return (
            datetime.fromtimestamp(
                (int.from_bytes(bytearray(data[start:end]), byteorder="little", signed=False,) / DIV) + OFFSET,
                timezone.utc,
            )
        )

    def _format_ppg(
            self, _, data: bytearray
    ) -> None:
        """
        Formats incoming ppg stream
        """
        def get_ppg_value(
                subdata: bytearray
        ) -> tuple:
            """
            Gets PPG value from subdata array
            """
            return struct.unpack("<i", subdata + (b'\0' if subdata[2] < 128 else b'\xff'))[0]
        # Append raw data plus timestamp
        if self.is_recording:
            self.raw_data['ppg'].append((datetime.now(tz=timezone.utc).strftime(TIME_FMT), data))
        # Calculate number of delta frames
        num = math.floor((len(data) - 10) / 12)
        # Iterate through the delta frames
        for x in range(num):
            sample = {
                'address': self.address,
                'desc': self.desc,
                'timestamp': datetime.now(tz=timezone.utc).strftime(TIME_FMT),
                'timestamp_polar': self._convert_to_timestamp(data, start=1, end=9).strftime(TIME_FMT),
            }
            # Iterate through bytes and get each PPG value
            for y in range(4):
                sample[f'ppg_{y}'] = get_ppg_value(data[10 + x * 12 + y * 3:(10 + x * 12 + y * 3) + 3])
            # Append the delta frame
            self._append_results(stream='ppg', data=sample)

    def _format_hr(
            self, _, data: bytearray
    ) -> None:
        """
        Appends reported heart rate and current OS time to HR list
        """
        # Append raw data plus timestamp
        if self.is_recording:
            self.raw_data['hr'].append((datetime.now(tz=timezone.utc).strftime(TIME_FMT), data))
        sample = {
            'address': self.address,
            'desc': self.desc,
            'timestamp': datetime.now(tz=timezone.utc).strftime(TIME_FMT),
            'heart_rate': data[1],
        }
        self._append_results(stream='hr', data=sample)

    def start_polar(
            self, record_start
    ):
        """
        Starts appending data to results lists
        """
        self.is_recording = True
        self.timer = record_start

    def stop_polar(
            self
    ) -> None:
        """
        Save and clear both data streams and report number of observations
        """
        report_data = []
        self.is_recording = False
        for k, v in self.results.items():
            report_data.append(self._save_data(data=v, ext=k))
        self.logger(self._report_results(streams=report_data))

    def _append_results(
            self, stream: str, data: dict
    ) -> None:
        """
        Appends results to required list and logs when data is received for the first time
        """
        # Check if this is the first time data has been received from a stream and log in GUI if so
        if self.is_firstrun[stream]:
            self.logger(f'{self.desc}: {stream.upper()} received')
            self.is_firstrun[stream] = False
        # If we're recording, append the results to the required list
        if self.is_recording:
            self.results[stream].append(data)

    def _save_data(
            self, data: list, ext='hr'
    ) -> tuple[str, bool]:
        """
        Saves given data as dataframe and pickle object, returns length of dataframe for reporting
        """
        # Construct filename from provided extension
        filename = f'{self.output_folder}/{self.timer.strftime(TIME_FMT_SAVE)}_{self.address.replace(":", "-")}_{ext}'
        # Construct dataframe
        df = pd.DataFrame(data,)
        # Save if data is present and return true for reporting
        if len(df) > 0:
            df.to_csv(f'{filename}.csv')
            data.clear()
            self._save_raw_data(fn=filename)
            return ext, True
        # If no data present, don't save and return false for reporting
        else:
            return ext, False

    def _save_raw_data(
            self, fn: str
    ) -> None:
        """
        Saves raw data as Python pickle file
        """
        # Construct filename
        filename = fn + "_raw.p"
        # Dump raw data as pickle file
        pickle.dump(self.raw_data, open(filename, "wb"))

    def _report_results(
            self, streams: dict
    ) -> str:
        """C
        onstruct report of recorded datastreams for logging in GUI
        """
        results = f'{self.desc}: '
        for dat, cond in streams:
            if cond:
                results += f'{dat.upper()} saved to {self.output_folder}.'
            else:
                results += f'{dat.upper()} did not report.'
        return results

    def quit_polar(
            self
    ) -> None:
        """
        Shut down the Bluetooth connection, called in GUI to allow application to finish successfully
        """
        self.running.set()


class Gui:
    """
    Basic Tkinter GUI to start, stop and log recordings made in multiple PolThreads.
    """
    def __init__(self, pol_details: list[tuple[str | list]]):
        self.is_recording: bool = False
        self.output_folder: str = os.getcwd()
        self.polthreads = self._init_polthreads(pol_details)
        self.root = self._init_root()
        self.logging_window = self._init_logging_window()
        self.logging_window.pack()
        self.start_button = self._init_start_button()
        self.start_button.pack()
        self.folder_select_button = self._init_folder_select_button()
        self.folder_select_button.pack()

    def _init_polthreads(
            self, pol_details
    ) -> list[PolThread]:
        """
        Creates polthread objects according to passed parameters
        """
        return [PolThread(address=polar, is_recording=self.is_recording, logger=self.log_text) for polar in pol_details]

    @staticmethod
    def _init_root(
    ) -> tk.Tk:
        """
        Initialises tkinter root and packs
        """
        # Create tkinter GUI root and set attributes
        root = tk.Tk()
        root.title('Polar Verity Sense Monitor')
        root.attributes('-topmost', 'true')
        # Create descriptive labels
        lab = tk.Label(root, text='Polar Verity Sense Monitor v.01')
        lab2 = tk.Label(root, text='© Huw Cheston, 2022 (hwc31@cam.ac.uk)')
        lab.pack()
        lab2.pack()
        return root

    def _init_folder_select_button(
            self
    ) -> tk.Button:
        """
        Initialises button to select output directory.
        """
        # Create button as variable first, as we need to pass it as an argument to its own command
        button = tk.Button(self.root, text='Select output folder',)
        button.configure(command=lambda: self.open_folder(button))
        return button

    def open_folder(
            self, button: tk.Button
    ) -> str:
        """
        Prompts for the user to select a directory for saving output results and passes to all PolThreads
        """
        # Prompt the user to select a directory
        f = filedialog.askdirectory(title='Open presets folder', initialdir=self.output_folder)
        # Tkinter returns an empty string if the directory isn't valid
        if f != '':
            self.output_folder = f
            button.configure(bg='green', text=f)
            # Send the selected output directory to all connected polthreads
            for polar in self.polthreads:
                polar.output_folder = self.output_folder
        # Display a visual element in the GUI to tell the user that the selected folder was invalid
        else:
            button.configure(bg='red', text='Invalid folder!')

    def _init_logging_window(
            self
    ) -> tk.scrolledtext.ScrolledText:
        """
        Initialises logging window
        """
        # Create the logging window
        return tk.scrolledtext.ScrolledText(
            self.root, height=5, width=30, state='disabled', wrap='word', font='TkDefaultFont'
        )

    def _init_start_button(
            self
    ) -> tk.Button:
        """
        Initialises recording start/stop button
        """
        button = tk.Button(
            self.root, text='Start recording...', bg='SystemButtonFace'
        )
        button.configure(command=lambda: self._start_button_command(button))
        return button

    def _start_button_command(
            self, button
    ):
        """
        Tells all connected PolThreads to start recording data
        """
        record_start = datetime.now()
        if self.is_recording:
            self.is_recording = False
            button.configure(bg='SystemButtonFace', text='Start recording..')
            for polar in self.polthreads:
                polar.stop_polar()
        elif not self.is_recording:
            self.is_recording = True
            button.configure(bg='green', text='Stop recording...')
            for polar in self.polthreads:
                polar.start_polar(record_start)

    def log_text(
            self, text: str
    ) -> None:
        """
        Logging function passes to connected PolThreads to add text to GUI
        """
        # Enable logging window
        self.logging_window.config(state='normal')
        # Add text passed as argument
        self.logging_window.insert('end', text + '\n')
        # Move logging window to end
        self.logging_window.see("end")
        # Disable logging window
        self.logging_window.config(state='disabled')

    def quit(
            self
    ) -> None:
        """
        Called when GUI is quit to pass exit function to connected PolThreads
        """
        for polar in self.polthreads:
            polar.quit_polar()


if __name__ == '__main__':
    polars = [
        ('A0:9E:1A:B2:2B:5B', 'CMS_1', ['ppg']),    # CMS 1 on armband
        ('A0:9E:1A:B2:2A:08', 'CMS_3', ['ppi']),   # CMS 3 on armband
    ]
    gui = Gui(pol_details=polars)
    gui.root.mainloop()
    gui.quit()
