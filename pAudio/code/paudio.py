#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    The Main pAudio module.

    - Loads the preamp module
    - Processing commands entry point: do()

"""

import os
import sys

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from common   import *
from services import preamp
from services import aux
from services import players


# COMMAND LOG FILE
LOGFNAME = f'{LOGFOLDER}/paudio_cmd.log'

if os.path.exists(LOGFNAME) and os.path.getsize(LOGFNAME) > 10e6:
    print ( f"{Fmt.RED}(paudio_) log file exceeds ~ 10 MB '{LOGFNAME}'{Fmt.END}" )

print ( f"{Fmt.BLUE}{Fmt.BOLD}(paudio) logging commands in '{LOGFNAME}'{Fmt.END}" )


def _init():
    run_drc2png()


def run_drc2png():
    """ Prepare DRC graphs
    """
    cmd = f'python3 {CODEFOLDER}/share/drc2png.py'
    sp.Popen(cmd, shell=True)


def do(cmd_phrase):

    prefix, cmd, args, add = read_cmd_phrase(cmd_phrase)
    result    = ''

    match prefix:

        case 'preamp':
            result = preamp.do(cmd, args, add)

        case 'aux':
            result = aux.do(cmd, args, add)

        # PENDING
        case 'player':
            result = 'WIP players'

        case _:
            # This should never occur because preamp is the defaulted as prefix
            result = 'unknown service'

    logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd_phrase}; {result}'

    with open(LOGFNAME, 'a') as FLOG:
            FLOG.write(f'{logline}\n')

    if type(result) != str:
        try:
            result = json.dumps(result)
        except Exception as e:
            result = f'Internal error: {e}'

    return result


_init()

