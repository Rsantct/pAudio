#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Restart the Spotify Desktop App in order to link it to the proper
    PipeWire-Jack sink after restarting the pAudio Jack process.

    We also RECOMMEND to minimize Spotify in order to stop
    Spotify main window to load lots of widgets with high CPU spense:

            apt install xdotool  (see below command line)


    usage:   spotify_desktop.py   start | stop

"""

import  sys
from    subprocess  import Popen, check_output, call
from    time        import sleep


def check_Spotify_Desktop_process():
    wait_sec = 15
    while wait_sec:
        tmp = check_output( 'pgrep -fli spotify | cut -d" " -f2',
                            shell=True).decode().split()
        if 'spotify' in tmp:
            print('(spotify_monitor) found Spotify Desktop running')
            sleep(3)    # wait a while extra to ensure communication
            return True
        wait_sec -= 1
        sleep(1)
    return False


def start():

    Popen('spotify 1>/dev/null 2>&1', shell=True)
    # Safe wait to ensure we can minimize the app in order to stop
    # Spotify main window to load lots of widgets...
    sleep(10)
    Popen('xdotool search --name Spotify windowminimize %@', shell=True)


    if not check_Spotify_Desktop_process():
        print('(spotify_monitor) Unable to detect Spotify Desktop running')
        sys.exit()


def stop():

    Popen('killall spotify', shell=True)


if sys.argv[1:]:

    if sys.argv[1] == 'stop':
        stop()

    elif sys.argv[1] == 'start':
        start()

    else:
        print(__doc__)

else:
    print(__doc__)
