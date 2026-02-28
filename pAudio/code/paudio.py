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
    print ( f"{Fmt.RED}(paudio) log file exceeds ~ 20 MB '{LOGFNAME}'{Fmt.END}" )

print ( f"{Fmt.BLUE}(paudio) logging commands in '{LOGFNAME}'{Fmt.END}" )


def _init():

    # Reset pAudio log
    with open(LOGFNAME, 'w') as FLOG:
        logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; STARTING pAudio (preamp & players)'
        FLOG.write(f'{logline}\n')
        logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; (i) will log only the commands that make changes.'
        FLOG.write(f'{logline}\n')

    # Prepare DRC FIR graphs
    sp.Popen(['python3', f'{CODEFOLDER}/share/drc_fir2png.py'])

    # Prepare DRC IIR graphs
    sp.Popen(['python3', f'{CODEFOLDER}/share/drc_iir2png.py'])


def do(cmd_phrase):

    prefix, cmd, args, add = read_cmd_phrase(cmd_phrase)
    result    = ''

    match prefix:

        case 'preamp':
            result = preamp.do(cmd, args, add)

        case 'player':
            result = players.do(cmd, args)

        # forwarding to paudio_ctrl.py server
        case 'ctrl':
            result = send_cmd( cmd_phrase, timeout=1, host=PAUDIO_ADDR, port=PAUDIO_PORT+1 )

        case _:
            # This should never occur because preamp is the defaulted as prefix
            result = 'unknown service'

    # LOG (paudio_ctrl has its own)
    if not prefix == 'ctrl':

        if cmd != 'state' and \
           not cmd.startswith('get_')  and not cmd.startswith('list_') and \
           not cmd.startswith('hi') and not cmd.startswith('hello'):

            logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {prefix} {cmd_phrase}; {result}'
            with open(LOGFNAME, 'a') as FLOG:
                    FLOG.write(f'{logline}\n')

    if type(result) != str:
        try:
            result = json.dumps(result)
        except Exception as e:
            result = f'Internal error: {e}'

    return result


_init()

