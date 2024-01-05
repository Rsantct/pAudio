#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Players subsystem.
    A DUMMY MODULE BY NOW
"""

import os
import sys
UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/paudio'
sys.path.append(f'{MAINFOLDER}/code/share')

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
