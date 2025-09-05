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


def clear_metadata():
    md = METATEMPLATE.copy()
    md["player"] = get_player_from_source()
    save_json_file(md, PLAYER_META_PATH)


def do_eject():

    try:
        if 'linux' in sys.platform:
            sp.Popen(['eject'])
            resu = 'ordered'

        elif 'darwin' in sys.platform:
            sp.Popen(['drutil', 'eject'])
            resu = 'ordered'

        else:
            resu = 'n/a'

    except Exception as e:
        print(f'(players) `eject` ERROR: {str(e)}')
        resu = str(e)

    return resu


def _init():

    clear_metadata()

    # MAIN LOOP to save player info to file
    if 'linux' in sys.platform:

        job = threading.Thread( target=linux.loop_save_player_info )

    elif 'darwin' in sys.platform:

        job = threading.Thread( target=macos.loop_save_player_info )

    print(f'{Fmt.BLUE}(players) Listening to playback status ...{Fmt.END}')
    job.start()


def get_all_info():
    """ A wrapper to get all playback related info at once,
        useful for web control clients querying
    """

    metadata = read_json_file(PLAYER_META_PATH)

    res = {
        'player':           metadata.get('player', ''),
        'state':            playback_control( 'state' ),
        'random_mode':      'n/a',
        'discid':           '',
        'metadata':         metadata
    }

    return res


def playback_control(cmd):

    if 'linux' in sys.platform:

        return linux.playback_control(cmd)

    elif 'darwin' in sys.platform:

        if cmd == 'pause':
            cmd = 'playpause'

        return macos.playback_control(cmd)

    else:
        return 'NAK'


# Entry function
def do(cmd, args):

    match cmd:

        case 'get_all_info':
            resu = get_all_info()

        case 'get_meta':
            resu = read_json_file(PLAYER_META_PATH)

        case 'eject':
            resu = do_eject()

        case _:
            resu = playback_control(cmd)

    return resu


_init()
