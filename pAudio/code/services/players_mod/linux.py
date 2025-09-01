#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

from   subprocess   import run as sp_run
from   time         import sleep
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "linux_mod"))

import spotify
import mpd_mod
import mplayer

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import  save_json_file, time_sec2hhmmss, read_json_file, \
                    METATEMPLATE, PLAYER_META_PATH, PREAMP_STATE_PATH


def loop_save_player_info(source=''):

    while True:

        metadata = get_player_info()

        for t in 'time_pos', 'time_tot':
            if metadata[t].startswith('00:'):
                metadata[t] = metadata[t][3:]

        save_json_file(metadata, PLAYER_META_PATH, timeout=0.5)

        sleep(1)


def get_player_info():
    """ Get player metadata as per the current pAudio source
    """

    res = METATEMPLATE

    source = read_json_file(PREAMP_STATE_PATH).get('source', 'none')
    s = source.lower()

    if s == 'spotify':
        res = spotify.get_spotify_info()

    elif s == 'mpd' or s == 'cd':
        res = mpd_mod.mpd_get_meta()

    elif 'tdt' in s or 'dvb' in s:
        res = mplayer.mplayer_get_meta('dvb')

    elif 'remote' in s:
        res["player"] = source.upper()

    else:
        res["player"] = source.upper()

    return res


def playback_change(player, cmd):
    """ as per the current pAudio source
    """

    player = player.lower()

    if player == 'spotify':
        res = spotify.spotify_control(cmd)

    elif player == 'mpd' or player == 'cd':
        res = mpd_mod.mpd_control(cmd)

    elif player == 'mplayer':
        res = mplayer.mplayer_control(cmd)

    else:
        res = 'n/a'

    return res


if __name__ == "__main__":

    print( json.dumps( get_player_info() ) )
