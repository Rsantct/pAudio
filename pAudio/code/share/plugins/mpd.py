#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    usage:  mpd.py      start | stop **

    Notice:

        (**) 'stop' will have NO EFFECT

        Some Desktop autostarts MPD when user logins, because of the packaged file:
            /etc/xdg/autostart/mpd.desktop

        If so, please set "X-GNOME-Autostart-enabled=false" inside that file.
"""

import sys
import os
from   subprocess import Popen, run, check_output

UHOME = os.path.expanduser("~")


def mpd_is_running():
    try:
        check_output(['pgrep',  '-f',  f'mpd {UHOME}/.mpdconf'])
        return True
    except:
        return False


def stop():
    #run( f'killall -KILL mpd', shell=True )
    print('(plugins/mpd.py) will not stop MPD anymore')


def start():

    if mpd_is_running():
        print('(plugins/mpd.py) MPD server already running')
    else:
        print('(plugins/mpd.py) running MPD server ...')
        Popen( f'mpd {UHOME}/.mpdconf', shell=True )


if __name__ == '__main__':

    if sys.argv[1:]:

        if sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'start':
            start()
        else:
            print(__doc__)

    else:
        print(__doc__)
