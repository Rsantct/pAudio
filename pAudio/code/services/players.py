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
sys.path.append(os.path.join(os.path.dirname(__file__), "players_mod"))

from    common      import *

if 'linux' in sys.platform:
    import linux

elif 'darwin' in sys.platform:
    import macos
    macos.PLAYERS_OF_INTEREST=['Spotify', 'Music']


def _init():

    save_json_file(METATEMPLATE, PLAYER_META_PATH)

    # MAIN LOOP to save player info to file
    if 'linux' in sys.platform:

        linux.PLAYER = 'Spotify'

        job = threading.Thread( target=linux.loop_save_player_info )

    elif 'darwin' in sys.platform:

        job = threading.Thread( target=macos.loop_save_player_info )

    print(f'{Fmt.BLUE}(players) Listening to playback status ...{Fmt.END}')
    job.start()


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
        return macos.playback_change(player, mode)

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


_init()
