#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    This is the launcher for the pAudio server and its child processes.

    Usage:

        start.py   start  |  stop

    NOTICE:

        A void CamillaDSP must be started before and outside this script
"""

import  sys
import  os
import  subprocess  as sp
from    time        import sleep, time
from    camilladsp  import CamillaClient

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')
sys.path.append(f'{MAINFOLDER}/code/services/preamp_mod')

from    common  import *

# import Jack stuff ONLY with LINUX
if sys.platform == 'linux' and CONFIG.get('jack'):
    import  jack
    from    jack_sources import SOURCES


def check_cdsp_running():
    """
    https://github.com/HEnquist/pycamilladsp/blob/master/camilladsp/datastructures.py

    RUNNING     Processing is running
    PAUSED      Processing is paused
    INACTIVE    CamillaDSP is inactive, and waiting for a new config to be supplied
    STARTING    The processing is being set up
    STALLED     The processing is stalled because the capture device isn't providing any data
    """

    # Temporay CamillaDSP client
    CC = CamillaClient('127.0.0.1', CONFIG["camilladsp_port"])

    try:
        CC.connect()

        s = CC.general.state()

        if 'RUNNING' in str(s) or 'INACTIVE' in str(s) or 'PAUSED' in str(s):
            if VERBOSE:
                print(f'{Fmt.BLUE}(start) CamillaDSP detected :-){Fmt.END}')
            return True
        else:
            print(f'{Fmt.RED}(start) Bad CamillaDSP state: {str(s)}{Fmt.END}')
            print(f'{Fmt.RED}(start) - check log folder -{Fmt.END}')
            return False

    except:
        print(f'{Fmt.RED}(start) Unable to connect to CamillaDSP, check log folder.{Fmt.END}')
        return False


def rewire_camilladsp():
    """ https://github.com/HEnquist/camilladsp?tab=readme-ov-file#jack

        CamillaDSP will emerge in Jack as "cpal_client_in" and "cpal_client_out",
        so CPAL acts as an intermediate layer.
    """

    def clear_camilla_input():
        """ Clearing inputs from system ports """

        cpal_in_ports = jcli.get_ports('cpal_client', is_input=True)

        for cp in cpal_in_ports:

            conns = None
            tries = 10
            while tries and not conns:

                conns = jcli.get_all_connections( cp )

                for c in conns:
                    if 'system' in c.name:
                        jcli.disconnect(c, cp)
                        print(f'{Fmt.GRAY}(start) clearing {c.name} -- {cp.name}{Fmt.END}')

                sleep(.2)
                tries -= 1

        # Checking clearing
        for cp in cpal_in_ports:
            conns = jcli.get_all_connections( cp )
            if conns:
                raise Exception(f'{Fmt.BOLD}(start) ERROR cannot clear: {cp.name} from system port{Fmt.END}')


    # Connecting pAudio `pre_in_loop` to CamillaDSP
    if VERBOSE:
        print(f'{Fmt.GRAY}(start) Trying to wire camillaDSP jack ports ...{Fmt.END}')

    try:
        jcli = jack.Client('tmp', no_start_server=True)
        jcli.activate()

        # clear camilladsp input from system
        clear_camilla_input()

        # wire camilladsp input
        jcli.connect('pre_in_loop:output_1', 'cpal_client_in:in_0')
        jcli.connect('pre_in_loop:output_2', 'cpal_client_in:in_1')

        del jcli

    except Exception as e:
        print(f'{Fmt.BOLD}(start) Cannot rewire camillaDSP jack ports: {str(e)}{Fmt.END}')


def run_plugins(mode='start'):
    """ Run plugins (stand-alone processes)
    """

    if not 'plugins' in CONFIG or not CONFIG["plugins"]:
        return

    if mode == 'start':
        for plugin in CONFIG["plugins"]:
            if VERBOSE:
                print(f'{Fmt.BLUE}{Fmt.BOLD}Running plugin: {plugin} ...{Fmt.END}')
            sp.Popen(f'{PLUGINSFOLDER}/{plugin} start', shell=True)

    elif mode == 'stop':
        for plugin in CONFIG["plugins"]:
            if VERBOSE:
                print(f'{Fmt.GRAY}Stopping plugin: {plugin} ...{Fmt.END}')
            sp.Popen(f'{PLUGINSFOLDER}/{plugin} stop', shell=True)


def prepare_jacktrip_server(iostat=False):
    """ run jacktrip in hub server mode
    """

    def jacktrip_wanted():

        jack_sources = CONFIG.get('jack', {}).get('sources', {})

        result = False

        for s, params in jack_sources.items():
            if params.get('jacktrip', None) == True:
                result = True

        return result


    if not jacktrip_wanted():
        print(f'{Fmt.GRAY}(start) (i) JackTrip server not needed{Fmt.END}')
        return

    log_path   = f'{MAINFOLDER}/log/jacktrip_hubserver.log'
    stats_path = f'{MAINFOLDER}/log/jacktrip_hubserver.stats'

    iostat_cmd = f' --iostat 5 --iostatlog '

    cmd = f'jacktrip --jacktripserver --numchannels 2 --nojackportsconnect'

    if iostat:
        cmd += iostat_cmd


    print(f'{Fmt.GRAY}(start) (i) Running JackTrip server ...{Fmt.END}')
    with open(log_path, 'w') as flog:
        sp.Popen(cmd, shell=True, stdout=flog, stderr=flog)


def prepare_zita_links():
    """ A LAN audio connection based on zita-njbridge from Fons Adriaensen.

            "similar to having analog audio connections between the
            sound cards of the systems using it"

        Further info at doc/80_Multiroom_pe.audio.sys.md

        Here we just prepare the addresses and ports mapping to use.
    """
    udp_port = CONFIG["jack"].get('zita_udp_base', 65000)

    # Iterare remoteSOURCES
    zita_link_udp_ports = {}
    for source_name, params in SOURCES.items():

        if not 'remote' in source_name:
            continue

        if VERBOSE:
            print( f'(start) preparing zita_link for: `{ source_name }`' )

        # Append the UPD_PORT to zita_link_udp_ports
        zita_link_udp_ports[source_name] = { 'addr':    params["ip"],
                                             'port':    params["port"],
                                             'udpport': udp_port}

        # (i) zita will use 2 consecutive ports, so let's space by 10 for simplicity
        udp_port += 10

    # (**) Saving the zita's UDP PORTS for future use because
    #     the remote sender could not be online at the moment ...
    with open(f'{LOGFOLDER}/zita_link_udp_ports', 'w') as f:
        d = json.dumps( zita_link_udp_ports, indent=2 )
        f.write(d)


def stop_zita_link():

    # Iterare remoteSOURCES
    for source_name, params in SOURCES.items():

        if not 'remote' in source_name:
            continue

        # REMOTE
        zita_remote_restart(params["ip"], params["port"], mode='stop')

        # LOCAL
        zita_local_restart(jport=params["jport"], mode='stop')


def manage_signal_detector(mode='start'):

    if mode == 'stop':
        print(f'{Fmt.GRAY}(start) killing JACK sources signal detector.{Fmt.END}')
        sp.Popen(['pkill', '-f', 'jack_sources_signal_detector'])
        return

    jack_signal_detector_path = f'{MAINFOLDER}/code/share/jack_sources_signal_detector.py'
    sp.Popen(['python3', jack_signal_detector_path])
    print(f'{Fmt.GRAY}{Fmt.BOLD}(start) starting JACK sources signal detector ...{Fmt.END}')


def stop_loudness_monitor():
    """ starting is in charge of preamp.py because the device can be changed when using CoreAudio
    """
    print(f'{Fmt.GRAY}(start) killing loudness monitor.{Fmt.END}')
    sp.Popen( 'pkill -KILL -f "loudness_monitor.py" 1>/dev/null 2>&1', shell=True )
    with open(LDMON_PATH, 'w') as f:
        f.write('{"LU_I": -99.0, "LU_M": -99.0, "scope": "album"}')

def stop():

    if VERBOSE:
        print(f'{Fmt.GRAY}{Fmt.BOLD}(start) Stopping pAudio server stuff ...{Fmt.END}')

    # Only macOS
    if sys.platform == 'darwin':
        macos.restore_playback_device( volume_dB = -30)

    # Plugins (stand-alone processes)
    run_plugins(mode='stop')

    # The server
    sp.Popen(['pkill', '-f',  'server.py paudio '])

    # Linux: Jack
    if sys.platform == 'linux' and CONFIG.get('jack'):

        # Zita network to jack (Linux)
        stop_zita_link()
        sleep(.25)

        # A forwarder of level changes to remote pAudio listeners
        sp.Popen(f'pkill -f remote_volume_daemon.py'.split())

        # JackTrip if used
        sp.Popen(['pkill', '-f', 'jacktrip'])

        # Optional
        if CONFIG["jack"].get('sources_auto_switch', False):
            manage_signal_detector('stop')

    # Stop standalone preocess loudness_monitor.py
    stop_loudness_monitor()

    sleep(1)


def start():

    def weird_camilladsp_ports():
        """ CamillaDSP, for unknown reason, sometimes emerged
            weird jack ports like `cpal_client_in-01`
        """
        result = False

        start_log_path = f'{MAINFOLDER}/log/start.log'
        try:
            with open(start_log_path, 'r') as f:
                tmp = f.read()
                if 'weird' in tmp.lower():
                    result = True
        except:
            print(f'{Fmt.BOLD}(start) cannot read {start_log_path}{Fmt.END}')

        return result


    def start_server(tries=1, max_tries=3):
        """ with recursive retries
        """

        t_srv_start = time()

        sp.Popen( srv_cmd.split() )

        if wait4server(timeout=server_timeout, verbose_seconds=5):
            t_srv_lapse = round(time() - t_srv_start, 1)
            print(f'{Fmt.BLUE}(start) pAudio server started in {t_srv_lapse} seconds :-){Fmt.END}')
            return True

        # Recursive retry
        else:
            if weird_camilladsp_ports() and tries < max_tries:
                print(f'{Fmt.BOLD}(start) detected weird CamillaDSP jack ports. WILL RETRY ...{Fmt.END}')
                return start_server(tries + 1)

            else:
                return False


    # Plugins (stand-alone processes)
    run_plugins()

    # restore Sound Card settings (currently only for Linux-ALSA)
    restore_sound_card()

    # Check if CamillaDSP is available
    if not check_cdsp_running():
        return

    # Run the pAudio main server 'paudio.py' to listen for commands
    srv_cmd = f'python3 {MAINFOLDER}/code/share/server.py paudio {CONFIG["paudio_addr"]} {CONFIG["paudio_port"]}'

    # Minimum timeout is 10 s
    server_timeout = max(10, estimate_server_response_delay() * 1.5)

    if VERBOSE:
        srv_cmd += ' -v'
    else:
        srv_cmd += f' 1>{LOGFOLDER}/paudio.log 2>{LOGFOLDER}/paudio.err'
        print(f"{Fmt.BLUE}(start) Waiting {server_timeout} s for the the pAudio server to run in background ...{Fmt.END}")


    if not start_server():
        print(f'{Fmt.RED}(start) No answer from `server.py paudio`, stopping all stuff.{Fmt.END}')
        stop()
        return

    # Linux with Jack
    if sys.platform == 'linux' and CONFIG.get('jack'):

        # JackTrip HUB server if needed
        prepare_jacktrip_server()

        # Zita network to jack receivers
        zitalink_job = threading.Thread(target=prepare_zita_links)
        zitalink_job.start()

        # A forwarder of level changes to remote pAudio listeners
        sp.Popen(f'python3 {UHOME}/pAudio/code/share/remote_volume_daemon.py start'.split())

        # Rewire CamillaDSP
        rewire_camilladsp()

        # Optional
        if CONFIG["jack"].get('sources_auto_switch', False):
            manage_signal_detector('start')


if __name__ == "__main__":

    mode    = ''
    VERBOSE = False

    for opc in sys.argv[1:]:

        if 'start' in opc:
            mode = 'start'

        elif 'stop' in opc:
            mode = 'stop'

        elif '-v' in opc:
            VERBOSE = True


    match mode:

        case 'start':
            start()

        case 'stop':
            stop()

        case _ :
            print(__doc__)
            sys.exit()
