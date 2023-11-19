#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Players subsystem.
"""

# This imports works because the main program server.py
# is located under the same folder than the commom module
from    common      import *


METATEMPLATE = {
                'player':       '',
                'time_pos':     '-',
                'time_tot':     '-',
                'bitrate':      '-',
                'artist':       '-',
                'album':        '-',
                'title':        '-',
                'track_num':    '-',
                'tracks_tot':   '-' }


def meta2disk(metadata):
    with open(PLAYER_META_PATH, 'w') as f:
        f.write( json.dumps(metadata) )


def init():
    meta2disk(METATEMPLATE)


# Entry function
def do(cmd, args, add):

    result  = 'void'

    return result


init()
