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

    from .players_mod import macos
    players_of_interest=['Spotify', 'Music']


def macos_loop():

    while True:

        m = macos.get_player_info( players_of_interest )

        save_json_file(m, PLAYER_META_PATH, timeout=0.5)

        sleep(1)


def init():

    save_json_file(METATEMPLATE, PLAYER_META_PATH, timeout=0.5)

    if 'darwin' in sys.platform:

        job = threading.Thread(target=macos_loop).start()
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

        #   Para UN player determinado
        #       tell application "Spotify"
        #           play            -- Reanuda
        #           pause           -- Pausa
        #           playpause       -- Alterna
        #           next track      -- Siguiente
        #           previous track  -- Anterior
        #       end tell
        #
        #   Para simular las Teclas Multimedia para el player de turno
        #       tell application "System Events"
        #           key code 16 -- Play/Pause
        #           key code 17 -- Next
        #           key code 15 -- Previous
        #       end tell

        pbk_script = f'''
            tell application "{player}"
                {mode}
            end tell
        '''
        macos._run_applescript(pbk_script)
        return 'ordered'

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
