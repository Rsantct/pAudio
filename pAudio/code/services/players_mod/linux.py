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
import remotes

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import  save_json_file, time_sec2hhmmss, read_json_file, \
                    METATEMPLATE, PLAYER_META_PATH, PREAMP_STATE_PATH, \
                    get_player_from_source, Fmt


def loop_save_player_info():

    while True:

        metadata = get_player_info()

        for k in 'time_pos', 'time_tot':
            if len(metadata.get(k, '')) > 5 and  metadata.get(k, '').startswith('00:'):
                metadata[k] = metadata[k][3:]

        save_json_file(metadata, PLAYER_META_PATH, timeout=0.5)

        sleep(1)


def get_player_info():
    """ Get player metadata as per the current pAudio source
    """

    res = METATEMPLATE

    player = get_player_from_source()
    lowplayer = player.lower()

    try:

        if lowplayer[:6] == 'remote':
            res = remotes.get_meta(remoteID=player)

        elif 'spotify' in lowplayer:
            res = spotify.get_spotify_info()

        elif 'mpd' in lowplayer or lowplayer == 'cd':
            res = mpd_mod.mpd_get_meta()

        elif 'mplayer' in lowplayer:
            res = mplayer.mplayer_get_meta('dvb')

        else:
            res["player"] = player if player else ''

    # This can happens if the player App is not ready at this moment
    except Exception as e:
        print(f'{Fmt.MAGENTA}(linux) ERROR getting metadata from {player}: {str(e)}{Fmt.END}')

    return res


def playback_control(cmd):
    """ as per the current pAudio source
    """

    player = get_player_from_source()
    lowplayer = player.lower()

    if lowplayer[:6] == 'remote':
        res = remotes.playback_control(player, cmd)

    elif 'spotify' in lowplayer:
        res = spotify.spotify_control(cmd)

    elif 'mpd' in lowplayer or lowplayer == 'cd':
        res = mpd_mod.mpd_control(cmd)

    elif 'mplayer' in lowplayer:
        res = mplayer.mplayer_control(cmd)

    else:
        res = 'n/a'

    return res


if __name__ == "__main__":

    print( json.dumps( get_player_info() ) )
