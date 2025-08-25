#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    The Main pAudio module, its main funtions are:

        - Loads the preamp module
        - Processing commands entry point: do()
        - Prepare png graph files of the loudspeaker's DRC

"""

import os
import sys

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from common   import *
from services import preamp
from services import players


# COMMAND LOG FILE
LOGFNAME = f'{LOGFOLDER}/paudio_cmd.log'

if os.path.exists(LOGFNAME) and os.path.getsize(LOGFNAME) > 20e6:
    print ( f"{Fmt.RED}(paudio_) log file exceeds ~ 20 MB '{LOGFNAME}'{Fmt.END}" )

print ( f"{Fmt.BLUE}(paudio) logging commands in '{LOGFNAME}'{Fmt.END}" )


def _init():

    # Prepare DRC FIR graphs
    cmd = f'python3 {CODEFOLDER}/share/drc_fir2png.py'
    sp.Popen(cmd, shell=True)

    # Prepare DRC IIR graphs
    cmd = f'python3 {CODEFOLDER}/share/drc_iir2png.py'
    sp.Popen(cmd, shell=True)


def do(cmd_phrase):

    prefix, cmd, args, add = read_cmd_phrase(cmd_phrase)
    result    = ''

    match prefix:

        case 'preamp':
            result = preamp.do(cmd, args, add)

        # PENDING
        case 'player':
            result = players.do(cmd, args)

        case _:
            # This should never occur because preamp is the defaulted as prefix
            result = 'unknown service'

    # LOG
    if cmd != 'state':
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

