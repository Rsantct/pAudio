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
    pass

elif 'darwin' in sys.platform:
    from .players_mod import players_macos


def macos_loop():

    while True:

        m = players_macos.get_player_info()

        save_json_file(m, PLAYER_META_PATH, timeout=0.5)

        sleep(1)


def init():

    save_json_file(METATEMPLATE, PLAYER_META_PATH, timeout=0.5)

    if 'darwin' in sys.platform:

        job = threading.Thread(target=macos_loop).start()
        print('listening to desktop players ...')


def get_all_info():

    m = read_json_file(PLAYER_META_PATH)

    res = {
        'state':            m.get('state'),
        'random_mode':      'n/a',
        'discid':           '',
        'metadata':         m
    }

    return res


# Entry function
def do(cmd, args):

    match cmd:

        case 'get_all_info':
            resu = get_all_info()

        case _:
            resu ='NAK'

    return resu


init()
