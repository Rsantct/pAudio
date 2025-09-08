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

from common import  save_json_file, time_sec2hhmmss, read_json_file,     \
                    PLAYERTEMPLATE, PLAYER_INFO_PATH, PREAMP_STATE_PATH, \
                    get_player_from_source, Fmt


def loop_save_player_info():
    """ This must be threaded
        Will loop every second
    """

    while True:

        player_info = get_player_info()

        for k in 'time_pos', 'time_tot':
            if len(player_info.get(k, '')) > 5 and  player_info.get(k, '').startswith('00:'):
                player_info[k] = player_info[k][3:]

        save_json_file(player_info, PLAYER_INFO_PATH, timeout=0.5)

        sleep(1)


def get_player_info():
    """ Get player info and metadata as per the current pAudio source
    """

    res = PLAYERTEMPLATE

    player = get_player_from_source()
    lowplayer = player.lower()

    try:

        if lowplayer[:6] == 'remote':
            res = remotes.get_info(remoteID=player)

        elif 'spotify' in lowplayer:
            res = spotify.get_info()

        elif 'mpd' in lowplayer or lowplayer == 'cd':
            res = mpd_mod.get_info()

        elif 'mplayer' in lowplayer:
            res = mplayer.get_info('dvb')

        else:
            res["player"] = player if player else ''

    # This can happens if the player App is not ready at this moment
    except Exception as e:
        print(f'{Fmt.MAGENTA}(linux) ERROR getting info and metadata from {player}: {str(e)}{Fmt.END}')

    return res


def playback_control(cmd):
    """ as per the current pAudio source
    """

    player = get_player_from_source()
    lowplayer = player.lower()

    if lowplayer[:6] == 'remote':
        res = remotes.playback_control(player, cmd)

    elif 'spotify' in lowplayer:
        res = spotify.playback_control(cmd)

    elif 'mpd' in lowplayer or lowplayer == 'cd':
        res = mpd_mod.playback_control(cmd)

    elif 'mplayer' in lowplayer:
        res = mplayer.playback_control(cmd)

    else:
        res = 'n/a'

    return res


if __name__ == "__main__":

    print( json.dumps( get_player_info() ) )
