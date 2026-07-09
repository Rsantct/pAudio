#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import os
import yaml

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'

def get_coreaudio_sources():
    """ config.yml syntax can have two flavours for the coreaudio/devices section

            - standard camillaDSP like (no pAudio source name is specified --> Desktop)
            - multiple capture devices as "pAudio sources" available in the Mac

        (see pAudio/doc config examples for more info)

        Be aware that CONFIG["coreaudio"] HAS NOT the original
        multiple capture devices tree if that flavour was used,
        CONFIG only has the first one found.

        So, we need to read again config/config.yml
    """

    cfg_path = f'{MAINFOLDER}/config/config.yml'

    with open(cfg_path, 'r') as f:
        cfg = yaml.safe_load( f.read() )

    coreaudio_capture = cfg["coreaudio"]["devices"]["capture"]

    if 'device' in coreaudio_capture:
        return { 'Desktop':  coreaudio_capture}

    else:
        return coreaudio_capture

