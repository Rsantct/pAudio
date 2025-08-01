#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import os
import sys
UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from   common   import *


SOURCES = {}


def _init():
    get_sources()


def get_sources():
    """
    """



    global SOURCES


    sources = {}

    SOURCES = sources

    return sources


def select(source):

    res = 'WIP'

    return res


_init()
