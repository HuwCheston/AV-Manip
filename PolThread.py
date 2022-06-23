import asyncio
import threading
from datetime import datetime, timezone
from bleak import BleakClient
import pandas as pd
import time
import pickle
import sys

pd.set_option('display.float_format', lambda x: '%.7f' % x)

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
START_PPG = bytearray(      # Open PPG stream
    [0x02, 0x01, 0x00, 0x01, 0x87, 0x00, 0x01, 0x01, 0x16, 0x00, 0x04, 0x01, 0x04]
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
div = 1000000000
offset = 946684800000000000 / div
time_fmt = '%Y-%m-%d %H:%M:%S.%f'   # strftime format
time_fmt_save = '%Y-%m-%d_%H-%M-%S'

"""DataFrame columns"""
PPG_COLS = ['epoch_time', 'self_time', 'data', 'polar_reported_sample_time']
OTHER_COLS = ['epoch_time', 'self_time', 'data', ]


class PolThread:
    """Receives heart rate and PPG data from a single Polar Verity Sense unit over Bluetooth LE"""
    def __init__(self, address, params):
        self.running = asyncio.Event()
        self.address = address
        self.params = params
        self.hr = []
        self.ppg = []
        self.ppi = []
        self.acc = []
        self.timer = datetime.now()
        self.client = BleakClient(self.address)
        threading.Thread(target=asyncio.run, args=(self._init_polar(),)).start()

    async def _init_polar(self):
        """Send bytes to PMD Control to start data streams and keep them alive until the GUI is closed"""
        try:
            await self.client.connect()
        # If no device was found, close PolThread
        except Exception as e:
            print(f'{e} Heartrate/PPG will not be tracked from this device!')
            sys.exit()   # This keeps the rest of the app alive
        else:
            # Send bytes to open PPG + HR streams
            await self.client.start_notify(UUID['PMD_Control'], self._report_init)
            await self.client.write_gatt_char(UUID['PMD_Control'], REQUEST_SETTINGS, response=True)
            await self.client.write_gatt_char(UUID['PMD_Control'], START_PPG, response=True)
            await self.client.write_gatt_char(UUID['PMD_Control'], START_ACC, response=True)
            await self.client.write_gatt_char(UUID['PMD_Control'], START_PPI, response=True)
            # Gather data from PPG and HR streams
            await self.client.start_notify(UUID['PMD_Data'], self._format_pmd_data)   # Receive PPG data
            await self.client.start_notify(UUID['HR_UUID'], self._format_hr)     # Receive HR data
            # Keep the connection alive until the signal is given to close
            await self.running.wait()   # Event set with call of polar.quit_python() in KeyThread

            # Close the Control, PPG, and HR streams
            try:
                await self.client.stop_notify(UUID['PMD_Control'])  # Stop PMD Control
                await self.client.stop_notify(UUID['PMD_Data'], )  # Stop PPG data
                await self.client.stop_notify(UUID['HR_UUID'])  # Stop HR data
                # Disconnect from the client
                await self.client.disconnect()
            except Exception as e:
                print(e)
            finally:
                sys.exit()

    def _report_init(self, _, data):
        """Report once correct response reported from device"""
        if data == bytearray(b'\xf0\x01\x01\x00\x00\x00\x01\x87\x00\x01\x01\x16\x00\x04\x01\x04'):  # success response
            print(f'{self.address}: initialised')

    def _format_pmd_data(self, _, data):
        """Gets timestamp from raw PPG bytes and appends Polar timestamp, OS timestamp, + PPG byte array to list"""
        li = [
            datetime.now().strftime(time_fmt),     # OS epoch time
            time.time() - self.timer.timestamp(),       # self time
            data        # data in form of bytesarray
        ]
        if data[0] == 0x01 and self.params['*recording']:   # 0x01 first byte means that data is from the PPG stream
            li.append(self._convert_to_timestamp(data, 1, 9).strftime(time_fmt))   # PPG stream also reports timestamp
            self.ppg.append(li)  # polar reported timestamp
        elif data[0] == 0x02 and self.params['*recording']:       # 0x02 first byte means that data is from ACC stream
            self.acc.append(li)
        elif data[0] == 0x03 and self.params['*recording']:     # 0x03 first byte means that data is from PPI stream
            self.ppi.append(li)

    @ staticmethod
    def _convert_to_timestamp(data, start, end):
        """Converts bytearray to timestamp"""
        return (
            datetime.fromtimestamp(
                (int.from_bytes(bytearray(data[start:end]), byteorder="little", signed=False,) / div) + offset,
                timezone.utc,
            )
        )

    def _format_hr(self, _, data):
        """Appends reported heart rate and current OS time to HR list"""
        if self.params['*recording']:
            self.hr.append(
                (datetime.now().strftime(time_fmt),    # OS epoch time
                 (time.time() - self.timer.timestamp()),    # self timer
                 data[1],   # heart rate BPM
                 )
            )

    def start_polar(self, record_start):
        """Starts appending data to HR/PPG lists"""
        self.timer = record_start
        return f'{self.address} started'

    def stop_polar(self):
        """Save and clear both data streams and report number of observations"""
        hr = self._save_data(data=self.hr, cols=OTHER_COLS, ext='hr')
        ppg = self._save_data(data=self.ppg, cols=PPG_COLS, ext='ppg')
        acc = self._save_data(data=self.acc, cols=OTHER_COLS, ext='acc')
        ppi = self._save_data(data=self.ppi, cols=OTHER_COLS, ext='ppi')
        return self._report_results(streams=[hr, ppg, acc, ppi])

    def _save_data(self, data, cols, ext='hr'):
        """Saves given data as dataframe and pickle object, returns length of dataframe for reporting"""
        # Construct filename from provided extension
        filename = f'output/biometrics/{self.timer.strftime(time_fmt_save)}_{self.address.replace(":", "-")}_{ext}'
        # Construct dataframe
        df = pd.DataFrame(data, columns=cols)
        # Save if data is present and return true for reporting
        if len(df) > 0:
            df.to_csv(f'{filename}.csv')
            pickle.dump(df, open(f'{filename}.p', 'wb'))
            data.clear()
            return ext, True
        # If no data present, don't save and return false for reporting
        else:
            return ext, False

    def _report_results(self, streams):
        """Construct report of recorded datastreams for logging in GUI"""
        results = f'{self.address}\n'
        for dat, cond in streams:
            if cond:
                results += f'{dat.upper()} reported.\n'
            else:
                results += f'{dat.upper()} did not report.\n'
        return results

    def quit_polar(self):
        """Shut down the Bluetooth connection, called when GUI closes to allow application to finish successfully"""
        self.running.set()
