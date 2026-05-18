#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

from   time         import sleep
import json
import os
import sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')
from common import  save_json_file, read_json_file, PLAYER_INFO_PATH

sys.path.append(os.path.join(os.path.dirname(__file__), "macos_mod"))
import macos_players

# Seconds to wait for the next playback info query and dump to disk
QUERY_LOOP_PERIOD = 1

def loop_save_player_info(source=''):
    """ This must be threaded
    """

    while True:

        player_info = get_player_info()

        for k in 'time_pos', 'time_tot':
            if len(player_info.get(k, '')) > 5 and  player_info.get(k, '').startswith('00:'):
                player_info[k] = player_info[k][3:]

        save_json_file(player_info, PLAYER_INFO_PATH, timeout=0.5)

        sleep(QUERY_LOOP_PERIOD)


def playback_control(cmd):
    """
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
    """

    player = read_json_file(PLAYER_INFO_PATH).get('player', '')

    if not player or player.lower == 'none':
        return 'n/a'

    pbk_script = f'''
        tell application "{player}"
            {cmd}
        end tell
    '''

    macos_player.run_applescript(pbk_script)

    return 'ordered'
