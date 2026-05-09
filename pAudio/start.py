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
from    time        import sleep, time
from    camilladsp  import CamillaClient

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')
sys.path.append(f'{MAINFOLDER}/code/services/preamp_mod')

from    common  import *

# import Jack stuff ONLY with LINUX
if sys.platform == 'linux' and CONFIG.get('jack'):
    import  jack_mod
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

    def cpal_alias():

        def do_alias():
            n = 3
            while n:
                try:
                    sp.check_output(f'jack_alias cpal_client_{io}:{io}_{p} camilladsp:{io}.{ch}',
                                    shell=True)
                    break
                except:
                    sleep(.5)
                    n -= 1
            if not n:
                return False
            else:
                return True

        result = []

        for io in ('in', 'out'):

            for p in ('0', '1'):
                ch = {'0':'L', '1':'R'}[p]
                result.append( do_alias() )

        if all(result):
            if VERBOSE:
                print(f'{Fmt.BLUE}(start) set alias for camillaDSP jack ports.{Fmt.END}')
        else:
            print(f'{Fmt.BOLD}(start) ERROR setting alias for camillaDSP jack ports.{Fmt.END}')

        return result


    # camillaDSP jack ports aliases
    cpal_alias()

    # Removing the CamillaDSP auto spawned Jack connections
    # and connecting pAudio `pre_in_loop` to CamillaDSP Jack port
    if VERBOSE:
        print(f'{Fmt.GRAY}(start) Trying to wire camillaDSP jack ports ...{Fmt.END}')

    # open a temporary jack.Client
    tmp = jack_mod._jcli_activate('wire_CamillaDSP')

    if tmp == 'done':

        # (i) system:capture ports may not exists, depending on sound card model
        if jack_mod.get_ports('system', is_physical=True, is_output=True):
            jack_mod.connect_bypattern('system',      'camilla', 'disconnect')

        jack_mod.connect_bypattern('pre_in_loop', 'camilla', 'connect'   )

        # close the temporary jack.Client
        del jack_mod.JCLI

    else:
        print(f'{Fmt.BOLD}(start) Cannot wire camillaDSP jack ports: {tmp}{Fmt.END}')


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


def manage_loudness_monitor_daemon(mode='start'):

    if mode == 'stop':

        if not process_is_running('loudness_monitor.py'):
            return()

        if VERBOSE:
            print(f'{Fmt.GRAY}(start) Stopping loudness_monitor.py{Fmt.END}')

        tmp = f'python3 {MAINFOLDER}/code/share/loudness_monitor.py stop'
        sp.call(tmp, shell=True)

    else:
        if VERBOSE:
            print(f'{Fmt.GRAY}(start) Running loudness_monitor.py in background ...{Fmt.END}')

        tmp = f'python3 {MAINFOLDER}/code/share/loudness_monitor.py start'
        sp.Popen(tmp, shell=True)


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


def stop():

    if VERBOSE:
        print(f'{Fmt.GRAY}{Fmt.BOLD}(start) Stopping pAudio server stuff ...{Fmt.END}')

    # Only macOS
    if sys.platform == 'darwin':
        macos.restore_playback_device()

    # Plugins (stand-alone processes)
    run_plugins(mode='stop')

    # The loudness_monitor daemon
    manage_loudness_monitor_daemon(mode='stop')

    # The server
    sp.Popen(['pkill', '-f',  'server.py paudio '])

    # Linux: Jack
    if sys.platform == 'linux' and CONFIG.get('jack'):

        # Zita network to jack (Linux)
        stop_zita_link()
        sleep(.25)
        sp.Popen(['pkill', '-f',  'jackd'])

        # JackTrip if used
        sp.Popen(['pkill', '-f', 'jacktrip'])

        # Optional
        if CONFIG["jack"].get('sources_auto_switch', False):
            manage_signal_detector('stop')

    sleep(1)


def start():

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

    t_srv_start = time()
    sp.Popen( srv_cmd.split() )

    if wait4server(timeout=server_timeout, verbose_seconds=5):
        t_srv_lapse = round(time() - t_srv_start, 1)
        print(f'{Fmt.BLUE}(start) pAudio server started in {t_srv_lapse} seconds :-){Fmt.END}')

    else:
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

        # Rewire CamillaDSP
        rewire_camilladsp()

        # Optional
        if CONFIG["jack"].get('sources_auto_switch', False):
            manage_signal_detector('start')

    # The loudness_monitor daemon
    manage_loudness_monitor_daemon()


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
