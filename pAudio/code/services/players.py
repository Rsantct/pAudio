#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Players subsystem.
"""

import time
import threading
import os
import sys
UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from    common      import *

if 'linux' in sys.platform:

    from .players_mod import linux
    linux.PLAYERS_OF_INTEREST=['Spotify', 'MPD']


elif 'darwin' in sys.platform:

    from .players_mod import macos
    macos.PLAYERS_OF_INTEREST=['Spotify', 'Music']


def init():

    save_json_file(METATEMPLATE, PLAYER_META_PATH, timeout=0.5)

    if 'darwin' in sys.platform:

        # LOOP to get MacOS player info
        job = threading.Thread( target=macos.loop_get_player_info )
        job.start()
        print(f'{Fmt.BLUE}(players) Listening to desktop players ...{Fmt.END}')


def get_all_info():

    m = read_json_file(PLAYER_META_PATH)

    res = {
        'player':           m.get('player', ''),
        'state':            m.get('state'),
        'random_mode':      'n/a',
        'discid':           '',
        'metadata':         m
    }

    return res


def playback_change(mode):

    player = get_all_info().get('player')

    if mode == 'pause':
        mode = 'playpause'


    if 'linux' in sys.platform:
        return 'WIP'

    elif 'darwin' in sys.platform:
        return macos.playback_change(mode)

    else:

        return 'NAK'


# Entry function
def do(cmd, args):

    match cmd:

        case 'get_all_info':
            resu = get_all_info()

        case 'play' | 'pause' | 'stop':
            resu = playback_change(mode=cmd)

        case _:
            resu ='NAK'

    return resu


init()
