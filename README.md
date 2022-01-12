# AV-Manip
Working repository for audio-visual manipulator

# Introduction
This project forms an early part of my PhD research into error correction procedures in improvised musical performances.
In its current state, the project consists of several Python scripts and a Reaper project file that enable a researcher to manipulate the performance of multiple improvising musicians in different ways, in an attempt to induce different breakdowns in their communication and monitor the repair strategies used.

# Experiment setup
The program is designed to be used during an experiment involving at least two musicians who are competent improvisers in any musical genre. 

Performers are seated so that direct visual communication is not possible. Instead, each musician watches a computer screen that, by default, contains a live video screen of the other musician(s). They also monitor the whole performance via headphones connected to an output channel in the Reaper DAW.

At the beginning of the experiment, the musicians are instructed to improvise together over a framework of their choosing (e.g. a jazz standard, a chord sequence or other framework). Once successful communication has been established, the researcher introduces a manipulation of the audio and visual feeds. This should cause a breakdown to a greater or lesser degree in the ensemble performance.

Finally, once the performance has broken down sufficiently, the researcher reverses the manipulations and the repair strategies used by the musicians are observed.

# Code overview

As a brief overview, this is what each of the files does:

-	Main.py creates a CamThread object for each USB camera detected, as well as a single ReaThread to manage Reapy and a KeyThread to send keypresses to OpenCV/Reaper.
-	KeyThread creates a blank OpenCV window that remains in focus on the researcher’s screen. This listens for keypresses and sends them to ReaThread and the CamThreads in order to start/stop manipulations. At the moment the commands are 1 or 2 on the keyboard to flip the video vertically or start a five-second video delay respectively. More can be added fairly easily with different lines in the params dictionary passed to each object. Pressing R resets the performer’s view and audio to live, and Q stops the recording and quits the program.
-	CamThread contains separate functions to read frames from the camera, display them on the performer’s screen (with modifications) and researcher’s screen (without modifications). The researcher’s screen is also recorded with ffmpeg. Each of these functions is on a separate thread, with the performer’s screen display function also listening to signals from the KeyThread.
-	At the moment, ReaThread merely starts recording on Reaper in sync with starting the ffmpeg recording and stops when it stops. 

# Requirements:
- Python 3.6 +
- OpenCV2
- FFMpeg
- Reaper 6.45 +
- Reapy (installed and configured to communicate with Reaper - check the documentation!)
