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
import  threading
from    camilladsp  import  CamillaClient
import  jack

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import *


CAMILLADSP_LAST_ERROR  = {}

LOGFNAME = f'{LOGFOLDER}/paudio_ctrl.log'
if os.path.exists(LOGFNAME) and os.path.getsize(LOGFNAME) > 10e6:
    print ( f"{Fmt.RED}(paudio_ctrl) log file exceeds ~ 10 MB '{LOGFNAME}'{Fmt.END}" )
print ( f"{Fmt.BLUE}(paudio_ctrl) logging commands in '{LOGFNAME}'{Fmt.END}" )

# The .aux_info file content
AUXINFO = {
    "loudspeaker":      CONFIG.get('loudspeaker', ''),
    "loudness_monitor": read_json_file(LDMON_PATH),
    "last_macro":       "",
    "warning":          "",
    "new_eq_graph":     False
}


def init():
    """ The .aux_info file can be used by others, for example
        preamp.py will alert there for eq_graph changes
    """

    global ONOFF_MODE, CAMILLADSP_LAST_ERROR

    # Reset paudio_ctrl.log
    with open(LOGFNAME, 'w') as FLOG:
        logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; STARTING paudio_ctrl'
        FLOG.write(f'{logline}\n')
        logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; (i) will log only the commands that make changes.'
        FLOG.write(f'{logline}\n')

    # ON/OFF button behavior (default pAudio)
    ONOFF_MODE = 'pAudio'
    if CONFIG.get('web_config'):
        onoff_mode = CONFIG.get('web_config', {}).get('onoff')
        if onoff_mode != None and 'amp' in onoff_mode:
            ONOFF_MODE = 'amplifier'

    # CamillaDSP monitoring
    CAMILLADSP_LAST_ERROR = get_camilladsp_last_error()
    loop_camilladsp_state2disk()

    # Monitor changes on eq.png
    loop_file_changed( f'{UHOME}/pAudio/code/share/www/public/images/eq.png',
                       flag_new_eq_graph )

    save_aux_info()


def save_aux_info():

    global CAMILLADSP_LAST_ERROR

    # Dynamic update <onoff>

    if ONOFF_MODE == 'amplifier':

        AUXINFO["onoff"] = amp_switch('state')

    elif ONOFF_MODE == 'pAudio':

        if process_is_running('paudio '):
            AUXINFO["onoff"] = 'on'
        else:
            AUXINFO["onoff"] = 'off'

    else:
        AUXINFO["onoff"] = '-'


    # Dynamic update <CamillaDSP ERROR>
    if CONFIG["expert_zone"]["camilladsp_xrun_monitor"]:

        curr_cdsp_error = get_camilladsp_last_error()

        if curr_cdsp_error != CAMILLADSP_LAST_ERROR:
            CAMILLADSP_LAST_ERROR = curr_cdsp_error
            AUXINFO["warning"] = curr_cdsp_error["error"]
            warning_expire(10)

    # Adding CamillaDSP state to .aux_info
    AUXINFO["CamillaDSP_state"] = get_camilladsp_state()

    # Adding Loudness Monitor to .aux_info
    if not 'running' in AUXINFO["CamillaDSP_state"].lower():
        # This clears residual values
        AUXINFO["loudness_monitor"]["LU_I"] = -99
        AUXINFO["loudness_monitor"]["LU_M"] = -99
    else:
        AUXINFO["loudness_monitor"] = read_json_file(LDMON_PATH)

    # Threading the .aux_info file saving
    save_job = threading.Thread( target=save_json_file, args=(AUXINFO, AUXINFO_PATH) )
    save_job.start()


def flag_new_eq_graph():
    AUXINFO['new_eq_graph'] = True
    save_json_file(AUXINFO, AUXINFO_PATH)
    sleep(2)
    AUXINFO['new_eq_graph'] = False
    save_json_file(AUXINFO, AUXINFO_PATH)


def loop_camilladsp_state2disk(period=3):

    def do_loop():

        while True:

            CC = CamillaClient('127.0.0.1', CONFIG["camilladsp_port"])

            try:
                CC.connect()
                st = CC.general.state().name
                CC.disconnect()

            except:
                st = 'NOT_AVAILABLE'

            with open(f'{LOGFOLDER}/camilladsp_state', 'w') as f:
                f.write( st )

            del(CC)

            sleep(period)


    jloop = threading.Thread( target=do_loop )
    jloop.start()


def get_camilladsp_state():

    try:
        with open(f'{LOGFOLDER}/camilladsp_state', 'r') as f:
            return f.read()
    except:
        return 'NOT_AVAILABLE'


def run_macro(mname):

    result = 'nothing to do'

    if not mname or 'clear_last' in mname:

        AUXINFO["last_macro"] = ''
        result = 'last_macro cleared'

    macro_path = f'{MACROSFOLDER}/{mname}'

    if os.path.isfile(macro_path):

        print( f'(ctrl) ordering macro: {mname}' )

        try:
            sp.Popen( [macro_path] )
            AUXINFO["last_macro"] = mname
            result = 'ordered'
        except Exception as e:
            result = f'Error running `{mname}`: {str(e)}'

    else:
        result = 'macro not found'


    save_aux_info()

    return result


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
    try:
        jcli = jack.Client(name='zitatmp', no_start_server=True)

    except Exception as e:
        print(f'{Fmt.RED}(paudio_ctrl) zita_j2n cannot open a jack client: {str(e)}{Fmt.END}')
        return 'cannot open a jack client'

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
    del jcli

    return result


def lu_monitor_manager(commandphrase):
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
        return f'ERROR writing FIFO `{LDCTRL_PATH}`: {str(e)}'


def restart_paudio(mode):

    if not mode in ('start', 'restart', 'stop', 'toggle', 'state'):
        return 'Needs `start| stop | state`'

    if mode == 'state':
        # trailing space is needed  to avoid confusion with the paudio_ctrl server
        return process_is_running('server.py paudio ')

    elif 'start' in mode:
        sp.Popen([f'{UHOME}/bin/paudio_restart.sh', 'start'])
        return 'Please wait a minute ...'

    elif mode == 'stop':
        sp.Popen([f'{UHOME}/bin/paudio_restart.sh', 'stop'])
        return 'Please wait a few ...'

    elif mode == 'toggle':

        if process_is_running('server.py paudio '):
            sp.Popen([f'{UHOME}/bin/paudio_restart.sh', 'stop'])
            return 'Please wait a few ...'

        else:
            sp.Popen([f'{UHOME}/bin/paudio_restart.sh', 'start'])
            return 'Please wait a minute ...'


def warning_expire(timeout=5):
    """ Threads a timer to clear the warning message field inside .aux_info
    """

    def mytimer(timeout):
        sleep(timeout)
        AUXINFO['warning'] = ''
        save_aux_info()

    job = threading.Thread(target=mytimer, args=(timeout,))
    job.start()


def warning_msg_manager(arg):
    """ Manages the warning field under .aux_info than can be used
        from the control web page interface
    """
    args = arg.split()

    if args[0] == 'set':

        if AUXINFO['warning']:
            result = 'warning message in use'
        else:
            AUXINFO['warning'] = ' '.join(args[1:])
            warning_expire(timeout=60)
            result = 'done'

    elif args[0] == 'perm':

        if AUXINFO['warning']:
            result = 'warning message in use'
        else:
            AUXINFO['warning'] = ' '.join(args[1:])
            result = 'done'

    elif args[0] == 'clear':
        AUXINFO['warning'] = ''
        result = 'done'

    elif args[0] == 'get':
        result = AUXINFO['warning']

    elif args[0] == 'expire':
        if args[1:] and args[1].isdigit():
            warning_expire(timeout=int(args[1]))
            result = 'done'
        else:
            result = 'bad expire timeout'
    else:
        result = 'usage: warning set message | warning clear'


    save_aux_info()

    return result


def manage_amp(amp_mode):

    amp_result = amp_switch( amp_mode )

    # Amplifier switch manages pAudio (default is True)

    AMP_PAUDIO  = CONFIG.get('amplifier_switch', {}).get('manage_pAudio', True)

    if amp_mode in ('on', 'off', 'toggle') and AMP_PAUDIO:

        # boolean
        paudio_curr = restart_paudio('state')

        if paudio_curr:
            if amp_result in ('off', '0', 0, False):
                restart_paudio('stop')
                warning_msg_manager('clear')
                warning_msg_manager('set pAudio will STOP.')

        else:
            if amp_result in ('on', '1', 1, True):
                restart_paudio('start')
                warning_msg_manager('clear')
                warning_msg_manager('set Please wait while starting pAudio ...')

    return amp_result


# Interface function for this module
def do( cmd_phrase):

    result = 'bad command'
    do_log = False

    prefix, cmd, args, _ = read_cmd_phrase(cmd_phrase)

    if prefix != 'ctrl':
        return 'bad commnad prefix'

    match cmd:

        case 'hello' | 'hi':
            result = 'paudio_ctrl'

        case 'aux_info':
            save_aux_info()
            result = AUXINFO

        case 'restart_paudio':
            result = restart_paudio( args )
            do_log = True

        case 'amp_switch':
            result = manage_amp(args)
            if args and not 'state' in args:
                do_log = True

        case 'get_paudio_config':
            result = json.dumps(CONFIG, indent=2)

        case 'get_web_config':
            result = get_web_config()

        case 'get_lu_monitor':
            result = read_json_file(LDMON_PATH)

        case 'reset_loudness_monitor' | 'reset_lu_monitor':
            result = lu_monitor_manager('reset')
            do_log = True

        case 'set_loudness_monitor_scope' | 'set_lu_monitor_scope':
            args = 'source' # FORCED to source
            result = lu_monitor_manager(f'scope={args}')
            do_log = True

        case 'zita_j2n':
            result = zita_j2n(args)
            do_log = True

        case 'run_macro':
            result = run_macro(args)
            do_log = True

        case 'warning':
            result = warning_msg_manager(args)
            do_log = True


    if do_log:
        logline = f'{strftime("%Y/%m/%d %H:%M:%S")}; {cmd} {args}; {result}'
        with open(LOGFNAME, 'a') as FLOG:
                FLOG.write(f'{logline}\n')

    if type(result) != str:
        result = json.dumps(result)

    return result


init()
