#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    The Main pAudio module.

    - Loads the preamp module
    - Processing commands entry point: do()
    - Run plugins (stand-alone processes)

"""

from  subprocess    import Popen
from  services      import preamp, aux, players

# This import works because the main program server.py
# is located under the same folder then the commom module
from  common import *


def run_plugins():
    """ Run plugins (stand-alone processes)
    """

    if not 'plugins' in CONFIG or not CONFIG["plugins"]:
        return

    for p in CONFIG["plugins"]:
        Popen(f'python3 {PLUGINSFOLDER}/{p} start', shell=True)


def run_drc2png():
    """ Prepare DRC graphs
    """
    cmd = f'python3 {CODEFOLDER}/share/drc2png.py'
    Popen(cmd, shell=True)


def do(cmd_phrase):

    prefix, cmd, args, add = read_cmd_phrase(cmd_phrase)
    result    = ''

    match prefix:

        case 'preamp':
            result = preamp.do(cmd, args, add)

        case 'aux':
            result = aux.do(cmd, args, add)

        # PENDING
        case 'players':
            pass

        case _:
            # This should never occur because preamp is the defaulted as prefix
            result = 'unknown service'


    if type(result) != str:
        try:
            result = json.dumps(result)
        except Exception as e:
            result = f'Internal error: {e}'

    return result


run_drc2png()

run_plugins()
