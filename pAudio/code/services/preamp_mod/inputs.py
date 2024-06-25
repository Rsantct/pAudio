#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import os
import sys
UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from common import *

import jack_mod

jack_mod._jcli_activate()


def select(name):

    jack_mod.clear_preamp()

    if name == 'none':
        return 'ordered'

    jack_pname = CONFIG["inputs"][name]["jack_pname"]

    return jack_mod.connect_bypattern(jack_pname, 'pre_in_loop')

