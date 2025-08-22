#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" A stand alone auxiliary service to remotely restart pAudio,
    and switch on/off tasks.

    This module is loaded by 'server.py', usually at pAudio's PORT + 1
"""
from    subprocess  import Popen
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import *


# COMMAND LOG FILE
LOGFNAME = f'{LOGFOLDER}/paudio_ctrl.log'

if os.path.exists(LOGFNAME) and os.path.getsize(LOGFNAME) > 10e6:
    print ( f"{Fmt.RED}(paudio_ctrl) log file exceeds ~ 10 MB '{LOGFNAME}'{Fmt.END}" )

print ( f"{Fmt.BLUE}(paudio_ctrl) logging commands in '{LOGFNAME}'{Fmt.END}" )


def restart_paudio(mode):

    if not mode:
        mode = 'state'

    if not mode in ('start', 'restart', 'stop', 'state'):
        return 'Needs `start| stop | state`'

    if mode == 'state':
        return process_is_running('camilladsp')

    elif 'start' in mode:
        sp.Popen(f'{UHOME}/bin/paudio_restart.sh start',  shell=True)
        return 'Please wait a minute ...'

    elif mode == 'stop':
        sp.Popen(f'{UHOME}/bin/paudio_restart.sh stop',  shell=True)
        return 'Please wait a few ...'


# Interface function for this module
def do( cmdphrase):

    result = 'bad command'

    cmd = arg = ''

    try:
        chunks = cmdphrase.split()
        cmd = chunks[0]
        if chunks[1:]:
            arg = chunks[1]
    except:
        pass

    match cmd:

        case 'restart_paudio':
            result = restart_paudio( arg )

        case 'amp_switch':
            result = amp_switch( arg )

        case 'get_web_config':
            result = get_web_config()


    logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {result}'

    with open(LOGFNAME, 'a') as FLOG:
            FLOG.write(f'{logline}\n')

    if type(result) != str:
        result = json.dumps(result)

    return result
