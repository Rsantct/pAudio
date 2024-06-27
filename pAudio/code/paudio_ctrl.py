#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" An auxiliary service to remotely restart pAudio,
    and switch on/off the system.

    This module is loaded by 'server.py', usually at pAudio's PORT + 1
"""
from    subprocess  import Popen
from    time        import  strftime
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import *


# COMMAND LOG FILE
logFname = f'{LOGFOLDER}/paudio_ctrl.log'
if os.path.exists(logFname) and os.path.getsize(logFname) > 10e6:
    print ( f"{Fmt.RED}(paudio_ctrl) log file exceeds ~ 10 MB '{logFname}'{Fmt.END}" )
print ( f"{Fmt.BLUE}(paudio_ctrl) logging commands in '{logFname}'{Fmt.END}" )


def restart_paudio(mode):

    if not mode in ('start', 'stop'):
        return 'must be restart_paudio  start|stop'

    sp.Popen(f'{MAINFOLDER}/start.py {mode}', shell=True)

    return 'ordered'


def manage_onoff(mode):

    if not mode in ('start', 'stop', 'toggle', 'state'):
        return 'Needs `start|stop|toggle`'

    if mode == 'state':
        return process_is_running('camilladsp')
    else:
        sp.Popen(f'{MAINFOLDER}/start.py {mode}', shell=True)
        return 'ordered'


# Interface function for this module
def do( cmdphrase):

    result = 'bad command'

    try:
        cmd = cmdphrase.split()[0]
        arg = cmdphrase.split()[-1]
    except:
        cmd = arg = ''

    match cmd:

        case 'restart_paudio':
            result = restart_paudio( arg )

        case 'amp_switch':
            result = manage_onoff( arg )


    logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd}; {result}'

    with open(logFname, 'a') as FLOG:
            FLOG.write(f'{logline}\n')

    if type(result) != str:
        result = json.dumps(result)

    return result
