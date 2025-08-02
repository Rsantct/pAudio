#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import os
import sys
UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from   common   import CONFIG


SOURCES = {}


def _init():
    get_sources()


def get_sources():
    """
    (i) THERE ARE TWO syntax options for Coreaudio capture device(s):

    coreaudio:

        devices:

            capture:

                ---------------------------------------------------------------
                Normal coreaudio input device directly specified:

                channels: 2
                device: BlackHole 2ch
                format: FLOAT32LE


                ---------------------------------------------------------------
                Alternative more than one section, to have source selection

                Mac Desktop:
                    channels: 2
                    device: BlackHole 2ch
                    format: FLOAT32LE

                TV:
                    channels: 2
                    device: UMC204HD 192k
                    format: S24LE
                ---------------------------------------------------------------


            playback:

                channels: 2
                device: Altavoces del MacBook Pro
                format: FLOAT32LE


    --> This function retrieves the ALTERNATIVE syntax sources is used
        OR { 'systemwide': {} } if normal syntax is used.

    """
    global SOURCES

    if CONFIG["coreaudio"]["devices"]["capture"].get('device'):
        SOURCES = { 'systemwide': {} }

    else:
        SOURCES = CONFIG["coreaudio"]["devices"].get('capture')

    return SOURCES



# (i) A select_source() function is not implemented here.
#     Preamp will use pcamilla.set_capture()


_init()
