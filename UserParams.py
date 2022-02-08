# These parameters can all be edited by the user before running the program
# TODO: add proper documentation for these parameters (this is outdated)
params = {
    'flipped': False,  # V: rotates orthogonally A: no modification
    'delayed': False,  # V: adds five-second delay A: adds five-second delay (not yet implemented)
    '*delay time': 1000,  # The default amount of time to delay V/A by. Can be changed in GUI
    '*max delay time': 10000,  # The max amount of time (ms) to allow V/A delay by. Affects memory consumption!
    # Will trigger an edit of Reaper JSFX parameters if exceeds currently set values.
    '*delay time presets': {
        'Short': 50,
        'Medium': 200,
        'Long': 1000,
        'Longer': 5000,
    },  # More presets can be added as above and will be configured to work automatically
    'blank face': False,
    'blank eyes': False,
    'loop rec': False,
    'loop play': False,
    'loop clear': False,
    'pause video': False,
    'pause audio': False,
    'pause both': False,
    '*pause frame': None,
    'control pitch': False,
    'control volume': False,
    '*reset audio': False,
    '*reset video': False,
    '*quit': False,
    # TODO: set this value to create tracks in ReaThread if not enough already exist
    '*participants': 1,  # Number of cameras to try and read
    '*fps': 30,     # 30 here works well for me!
    # Add more parameters as here...
    # Params beginning with * are system parameters and will not be displayed in GUI
}
