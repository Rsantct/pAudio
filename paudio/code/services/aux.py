#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Aux subsystem.
"""

# This import works because the main program server.py
# is located under the same folder than the commom module
from    common      import *


def init():
    """ The .aux_info file can be used by others, for example
        preamp.py will alert there for eq_graph changes
    """

    global AUXINFO, LU_MON_ENABLED

    LU_MON_ENABLED  = True if 'loudness_monitor.py' in CONFIG["plugins"] \
                           else False

    AUXINFO = {
        "amp":              "on",
        "loudness_monitor": read_json_file(LDMON_PATH),
        "last_macro":       "",
        "warning":          "",
        "new_eq_graph":     False
    }
    save_aux_info()


def save_aux_info():
    """ this must be threaded """
    def dosave():
        save_json_file(AUXINFO, AUXINFO_PATH)
    job = threading.Thread(target=dosave,)
    job.start()


def manage_lu_monitor(commandphrase):
    """ Manages the loudness_monitor.py daemon through by its fifo
    """
    #   As per LDCTRL_PATH is a namedpipe (FIFO), it is needed that
    #   'loudness_monitor.py' was alive in order to release any write to it.
    #   If not alive, any f.write() to LDCTRL_PATH will HANG UP
    #   :-(
    if not process_is_running('loudness_monitor.py'):
        return 'ERROR loudness_monitor.py NOT running'

    try:
        with open(LDCTRL_PATH, 'w') as f:
            f.write(commandphrase)
        return 'ordered'
    except Exception as e:
        return f'ERROR writing FIFO \`{LDCTRL_PATH}\`: {str(e)}'


def manage_onoff(mode):
    """ currently only force to stop all stuff
    """
    print(f'{Fmt.BOLD}BYE !{Fmt.END}')

    # Forced stop
    #sp.Popen('pkill -KILL -f "\/paudio"', shell=True)

    # A clean stop, restoring audio playback device and volume
    sp.Popen(f'{MAINFOLDER}/paudio.sh stop', shell=True)

    sys.exit()


# Entry function
def do(cmd, args, add):

    result  = 'nothing was done'

    match cmd:

        case 'get_web_config':
            result = {  'main_selector':        'inputs',
                        'LU_monitor_enabled':   LU_MON_ENABLED
            }

        case 'get_lu_monitor':
            result = read_json_file(LDMON_PATH)

        case 'info':
            AUXINFO["loudness_monitor"] = read_json_file(LDMON_PATH)
            save_aux_info()
            result = AUXINFO

        case 'reset_loudness_monitor' | 'reset_lu_monitor':
            result = manage_lu_monitor('reset')

        case 'set_loudness_monitor_scope' | 'set_lu_monitor_scope':
            args = 'input' # FORCED to input
            result = manage_lu_monitor(f'scope={args}')

        case 'amp_switch':
            result = manage_onoff(args)


    return result


init()
