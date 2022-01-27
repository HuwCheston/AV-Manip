import fileinput
import re


def edit_reaper_fx(params):
    fx_location = './Reaper/Effects/midi/'
    files = {
        fx_location + 'midi_delay': params['*max delay time'],
    }

    # TODO: adjust this code if more Reaper JSFX parameter files need to be adjusted to match OpenCV (works for now)
    for file in files.keys():
        with open(file) as f:
            data = f.readlines()
        result = re.search("slider1:0<0,(.*),1>Delay", str(data[2]))
        if int(result.group(1)) != params['*max delay time'] and isinstance(params['*max delay time'], int):
            data[2] = "slider1:0<0," + str(params['*max delay time']) + ",1>Delay (ms)" + "\n"
            new_file = open(file, "w")
            new_file.writelines(data)
            new_file.close()
            print(f"Rewrote {file}, line {data[2]}Will need to recompile FX!")
