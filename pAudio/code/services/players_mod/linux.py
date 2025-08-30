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

from common import  save_json_file, time_sec2hhmmss, \
                    METATEMPLATE, PLAYER_META_PATH


# List of players to be queried so that the response will be faster.
# Set void to query all in _PLAYERS
PLAYERS_OF_INTEREST=['Spotify', 'MPD']

_PLAYERS = {
    'Spotify':  spotify.get_spotify_info,
    'MPD':      mpd_mod.mpd_get_meta
}


def loop_save_player_info(source=''):

    while True:

        metadata = get_player_info(source)

        save_json_file(metadata, PLAYER_META_PATH, timeout=0.5)

        sleep(1)


def get_player_info(source='none'):
    """
    """

    res = METATEMPLATE

    if source.lower() == 'spotify':
        res = spotify.get_spotify_info()

    if source.lower() == 'mpd':
        res = mpd_mod.mpd_get_meta()

    for t in 'time_pos', 'time_tot':
        if res[t].startswith('00:'):
            res[t] = res[t][3:]

    return res


if __name__ == "__main__":

    print( json.dumps( get_player_info('spotify') ) )
