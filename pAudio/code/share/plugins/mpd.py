#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    usage:  mpd.py      start | stop

    Notice:

        Some Desktop autostarts MPD when user logins, because of the packaged file:
            /etc/xdg/autostart/mpd.desktop

        If so, please set "X-GNOME-Autostart-enabled=false" inside that file.
"""
import sys
import os
from subprocess import Popen

UHOME = os.path.expanduser("~")


def stop():
    Popen( f'mpd --kill', shell=True )

def start():
    Popen( f'mpd {UHOME}/.mpdconf', shell=True )


if __name__ == '__main__':

    if sys.argv[1:]:

        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            stop()
            start()
        else:
            print(__doc__)

    else:
        print(__doc__)
