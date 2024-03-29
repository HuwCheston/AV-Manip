import threading
import time
import os
from datetime import datetime
import tkinter
from TkGui import TkGui
from PolThread import PolThread
import shutil


class KeyThread:
    def __init__(self,
                 params: dict,
                 stop_event: threading.Event,
                 reathread,
                 camthread: list,):
        self.name = 'Keypress Manager'
        self.stop_event = stop_event
        self.params = params

        self.gui = TkGui(params=self.params, keythread=self)
        self.polthread = [PolThread(address=add, params=params, logger=self.gui.log_text)
                          for add
                          in self.params['*polar mac addresses']]
        self.reathread = reathread
        self.camthread = camthread
        self.start_keymanager()

    def start_keymanager(self):
        self.gui.tk_setup()
        self.main_loop()

    def main_loop(self):
        self.gui.root.mainloop()

    def exit_loop(self):
        self.reset_manips()
        # for num in range(self.params['*exit time'], 0, -1):
        #     # Wait to make sure everything has shut down (prevents tkinter RunTime errors w/threading)
        #     time.sleep(1)
        # If we're recording, stop first
        if self.reathread.project.is_recording:
            self.stop_recording()
        self.stop_event.set()
        for pol in self.polthread:
            pol.quit_polar()
        self.gui.root.destroy()

    def enable_manip(self, manip, button):
        self.reset_manips()
        self.params[manip] = True
        button.config(bg='green')
        self.gui.log_text(text=f'{manip} now active.')

    def reset_manips(self):
        # TODO: refactor this into seperate functions
        self.gui.log_text(text='Resetting...')
        self.params['*reset video'] = True  # This param is reset to False by CamThread once resetting has completed
        for param in self.params.keys():
            if isinstance(self.params[param], bool) and not param.startswith('*'):
                self.params[param] = False
        for b in self.gui.buttons_list:
            try:
                b.config(bg="SystemButtonFace")
            except tkinter.TclError:
                pass
        # Allows time for all threads relying on params being true to finish. This helps avoid the reaper socket closing
        # unexpectedly if it tries to execute two commands simultaneously (e.g. setting delay time, turning off fx)
        time.sleep(0.3)
        self.reathread.reset_manips()
        self.gui.log_text(text='done!')

    def start_recording(self, bpm,):
        record_start = datetime.now()
        # We need to reset all of our manips before starting the recording (can turn them on after)
        self.reset_manips()
        # Start the recording in both reathread and for all of our camthreads
        self.reathread.start_recording(bpm,)
        for cam in self.camthread:
            threading.Thread(
                target=cam.cam_write.start_recording,
                args=([record_start, self.params['*resolution']])
            ).start()
            threading.Thread(
                target=cam.performer_cam_write.start_recording,
                args=([record_start, self.params['*resolution']])
            ).start()
        self.params['*recording'] = True  # This parameter is used to add text onto the camera view
        for pol in self.polthread:
            pol.start_polar(record_start)
        self.gui.log_text(text=f'Started recording at {record_start.strftime("%H:%M:%S")}')

    def stop_recording(self):
        self.params['*recording'] = False    # This parameter is used to remove text from the camera view
        # We need to reset all of our manips before stopping the recording (can turn them on after)
        self.reset_manips()
        # Stop the recording in both reathread and for all our camthreads
        self.reathread.stop_recording()
        for cam in self.camthread:
            cam.cam_write.stop_recording()
            cam.performer_cam_write.stop_recording()
        for pol in self.polthread:
            pol.stop_polar()
        self.gui.log_text(text=f'Finished recording at {datetime.now().strftime("%H:%M:%S")}')
        self.backup_output()

    def backup_output(self):
        """Automatically backs up output to specified directories after each recording"""
        # Iterate through all backup folders
        for folder in self.params['*backup directory']:
            # Make a new folder in our backup directory
            try:
                backup_dir = fr"{folder}\output_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
                os.mkdir(backup_dir)
            except FileNotFoundError:
                self.gui.log_text(f'Backup directory {folder} not present')
            else:
                # Iterate through our output files and copy them to the backup directory
                for (root, dirs, files) in os.walk(r".\output", topdown=False):
                    for name in files:
                        try:
                            shutil.copy(os.path.join(root, name), backup_dir)
                        except PermissionError:
                            self.gui.log_text(f'Permission denied when backing up {name}')
                        except FileExistsError:
                            self.gui.log_text(f'File already exists when backing up {name}')
