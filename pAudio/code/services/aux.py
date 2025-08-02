#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Aux subsystem.
"""

import os
import sys
import jack

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from common import *


def init():
    """ The .aux_info file can be used by others, for example
        preamp.py will alert there for eq_graph changes
    """

    global AUXINFO


    AUXINFO = {
        "amp":              "on",
        "loudness_monitor": read_json_file(LDMON_PATH),
        "last_macro":       "",
        "warning":          "",
        "new_eq_graph":     False
    }
    save_aux_info()


def zita_j2n(args):
    """ This internal function is always issued from a multiroom receiver.

        Feeds the preamp audio to a zita-j2n port pointing to the receiver.

        args: a json tuple string "(dest, udpport, do_stop)"
    """

    dest, udpport, do_stop = json.loads(args)

    # BAD ADDRESS
    if not is_IP(dest):
        return 'bad address'

    zitajname = f'zita_j2n_{ dest.split(".")[-1] }'

    # STOP mode
    if do_stop == 'stop':
        zitapattern  = f'zita-j2n --jname {zitajname}'
        sp.Popen( ['pkill', '-KILL', '-f',  zitapattern] )
        return f'killing {zitajname}'

    # NORMAL mode
    jcli = jack.Client(name='zitatmp', no_start_server=True)

    jports = jcli.get_ports()

    result = ''

    if not [x for x in jports if zitajname in x.name]:
        zitacmd     = f'zita-j2n --jname {zitajname} {dest} {udpport}'
        with open('/dev/null', 'w') as fnull:
            sp.Popen( zitacmd.split(), stdout=fnull, stderr=fnull )

    wait4ports(zitajname, timeout=3)

    try:
        jcli.connect( 'pre_in_loop:output_1', f'{zitajname}:in_1' )
        jcli.connect( 'pre_in_loop:output_2', f'{zitajname}:in_2' )
        result = 'done'

    except Exception as e:
        result = str(e)

    jcli.close()

    return result


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


# Entry function
def do(cmd, args, add):

    result  = 'nothing was done'

    match cmd:

        case 'echo' | 'hello':
            result = 'ACK'

        # LU_monitor_enabled is a legacy option, now it is always enabled.
        case 'get_web_config':
            result = {  'main_selector':        'sources',
                        'LU_monitor_enabled':   True
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

        case 'zita_j2n':
            result = zita_j2n(args)

    if type(result) != str:
        result = json.dumps(result)

    return result


init()
