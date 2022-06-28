# These parameters can be edited by the user before running the program and should adjust system settings automatically
cascade_location = r".\venv\Lib\site-packages\opencv_python-4.5.5.62.dist-info"
user_params = {
    # TODO: set this value to create more tracks in ReaThread if not enough exist already
    '*participants': 1,     # Number of cameras/tracks to try and read
    '*polar mac addresses': [
        'A0:9E:1A:AD:16:3B',    # My personal Polar Verity Sense: marked 'H' on armband
        'A0:9E:1A:B2:2B:5B',    # CMS 1 on armband
        'A0:9E:1A:B2:2B:B6',    # CMS 2 on armband
        'A0:9E:1A:B2:2A:08',    # CMS 3 on armband
    ],

    '*fps': 30,     # Try and set camera FPS to this value (and adjust all params that require this as needed)
    '*resolution': '640x480',   # Camera resolution (for researcher view and recording)
    '*scaling': 2.0,     # Amount to scale up the performer camera view by
    '*exit time': 3,    # Number of seconds to wait before exiting the program

    '*default bpm': 120,    # The default BPM to use in Reaper: can be overridden in the GUI
    '*default count-in': 4,     # The default number of count-in bars to use in Reaper: can be overridden in the GUI

    '*delay time': 1000,    # The default delay time (<= max delay time: can be changed when program is running)
    '*max delay time': 10000,   # The maximum amount of time available for delay (will configure Reaper JSFX if needed)
    '*delay time presets': {    # Preset delay times to display in GUI (must be <= max delay time)
        'Short': 50,
        'Medium': 200,
        'Long': 1000,
        'Longer': 5000,
        # Add more delay presets here - they will be configured in the GUI automatically
    },
    '*var delay samples': 1000,  # Number of samples to draw when creating variable delay distributions.
    '*var delay distributions': {
        "Uniform": {    # Name of the distribution to be displayed in the combobox
            "text": ["Low:", "High:"],  # Options to be displayed next to the two entry fields
            "function": "np.random.uniform",    # Numpy function used to create the distribution as ndarray
        },
        "Gaussian": {
            "text": ["Mu:", "Sigma:"],
            "function": "np.random.normal",
        },
        "Poisson": {
            "text": ["Expected:", "N/A:"],
            "function": "np.random.poisson",
        },  # Add more distributions here in the format above - they will be configured in the GUI automatically
    },
    '*incremental delay distributions': [
        'Linear',
        'Exponential',
        'Natural Log'
    ]
    # Add more distributions here in the format above - they will be configured in the GUI automatically
}

# These parameters should not be adjusted by the user (unless to add more manipulations)
sys_params = {
    'flipped': False,  # Rotates video orthogonally: used as a test manipulation, unlikely to be useful

    'delayed': False,  # Adds delay of X seconds to video and audio: amount of delay can be adjusted

    'blank face': False,    # Uses ML (Haar-like) to blank performers face. Error detection in place.
    'blank eyes': False,    # Uses ML (Haar-like) to blank performers eyes. Some error detection in place, improvable?

    'loop rec': False,  # Starts recording video for later playback
    'loop play': False,  # Plays previously recorded video
    'loop clear': False,    # Clears any previously recorded video from memory
    '*loop params': {
            "frames": [],
            "var": 0,
            "has_loop": False,
        },

    'pause video': False,   # Stops performer's view of video
    'pause audio': False,   # Stops performer's audio
    'pause both': False,    # Stops performer's audio and video channel
    '*pause frame': None,   # Stores the video frame immediately before implementing the pause

    'control pitch': False,     # Not implemented
    'control volume': False,    # Not implemented

    '*reset audio': False,  # Resets audio back to normal (i.e. no manipulations)
    '*reset video': False,  # Resets video back to normal (i.e. no manipulations)
    '*recording': False,
    '*quit': False,     # Quits the program
}

params = user_params | sys_params

# TODO: refactor the (changeable) user params and the (unchangeable) system params into two seperate dictionaries.
#  The user params should be changeable in a .txt file, and then joined with the system params into one dictionary
#  when the program runs (with checks to ensure that they don't conflict, e.g. delay presets out of range!)
