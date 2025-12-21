#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    This is the launcher for the pAudio server and its child processes.

    Usage:

        start.py   start  |  stop  | --jack

        --jack  will only run Jack as per the configuration under pAudio/config.yml

    NOTICE:

        A void CamillaDSP must be started before and outside this script
"""

import  sys
import  os
from    time        import sleep
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
    HOST = '127.0.0.1'
    PORT = 1234
    CC   = CamillaClient(HOST, PORT)

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


def prepare_jack_stuff():
    """ execute JACK with the convenient loops
    """

    if sys.platform != 'linux':
        print(f'{Fmt.RED}(start) JACK only on Linux{Fmt.END}')
        return

    jloops_list = ['pre_in_loop']

    if any('mpd' in p for p in CONFIG["plugins"]):
        jloops_list.append('mpd_loop')

    fs       = CONFIG["samplerate"]
    alsa_dev = CONFIG["jack"]["device"]
    period   = CONFIG["jack"]["period"]
    nperiods = CONFIG["jack"]["nperiods"]
    dither   = CONFIG["jack"]["dither"]

    if not jack_mod.run_jackd(  alsa_dev=alsa_dev,
                                fs=fs, period=period, nperiods=nperiods,
                                jloops_list=jloops_list, dither=dither):

        print(f'{Fmt.BOLD}(start) Cannot run JACKD. See log folder. Exiting :-({Fmt.END}')
        sys.exit()

    # **PipeWire** needs to detect this new Jack and connect to it
    if process_is_running('pipewire'):

        try:
            sp.call( 'systemctl --user restart pipewire', shell=True)
            if VERBOSE:
                print(f'{Fmt.BLUE}(start) Reloading PipeWire for jack-sink ...{Fmt.END}')

        except Exception as e:
            print(f'{Fmt.BOLD}(start) Problems restarting PipeWire: {str(e)}{Fmt.END}')


def rewire_camilladsp():
    """ https://github.com/HEnquist/camilladsp?tab=readme-ov-file#jack

        CamillaDSP will show up in Jack as "cpal_client_in" and "cpal_client_out".
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
    jack_mod._jcli_activate('wire_CamillaDSP')


    # (i) system:capture ports may not exists, depending on sound card model
    if jack_mod.get_ports('system', is_physical=True, is_output=True):
        jack_mod.connect_bypattern('system',      'camilla', 'disconnect')

    jack_mod.connect_bypattern('pre_in_loop', 'camilla', 'connect'   )

    # close the temporary jack.Client
    del jack_mod.JCLI


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


def start_zita_link():
    """ A LAN audio connection based on zita-njbridge from Fons Adriaensen.

            "similar to having analog audio connections between the
            sound cards of the systems using it"

        Further info at doc/80_Multiroom_pe.audio.sys.md
    """

    try:
        tmp = CONFIG["jack"].get('zita_udp_base')

        if type(tmp) == int:
            UDP_PORT = tmp
        else:
            raise Exception("BAD VALUE 'zita_udp_base'")

    except Exception as e:
        UDP_PORT = 65000
        print(f'{Fmt.RED}(start) ERROR in config.yml: {str(e)}, using {UDP_PORT} {Fmt.END}')

    try:
        tmp = CONFIG["jack"].get('zita_buffer_ms')

        if type(tmp) == int:
            ZITA_BUFFER_MS = tmp
        else:
            raise Exception("BAD VALUE 'zita_buffer_ms'")

    except Exception as e:
        ZITA_BUFFER_MS = 20
        print(f'{Fmt.RED}(start) ERROR in config.yml: {str(e)}, using {ZITA_BUFFER_MS} {Fmt.END}')


    zita_link_udp_ports = {}

    # SOURCES example see stop_zita_link() below
    for source_name, params in SOURCES.items():

        if not 'remote' in source_name:
            continue

        if VERBOSE:
            print( f'(start) Running zita-njbridge for: `{ source_name }`' )

        # Trying to RUN THE REMOTE SENDER zita-j2n (**)
        if VERBOSE:
            print(f'{Fmt.GRAY}(start) starting remote zita-j2n at: {params["ip"]}{Fmt.END}')
        remote_zita_restart(params["ip"], params["port"], UDP_PORT)

        # Append the UPD_PORT to zita_link_udp_ports
        zita_link_udp_ports[source_name] = { 'addr':    params["ip"],
                                             'port':    params["port"],
                                             'udpport': UDP_PORT}

        # RUN LOCAL RECEIVER:
        if VERBOSE:
            print(f'{Fmt.GRAY}(start) running local zita-n2j: {params["jport"]}{Fmt.END}')
        local_zita_restart( params["ip"], UDP_PORT, ZITA_BUFFER_MS )

        # (i) zita will use 2 consecutive ports, so let's space by 10
        UDP_PORT += 10

    # (**) Saving the zita's UDP PORTS for future use because
    #     the remote sender could not be online at the moment ...
    with open(f'{LOGFOLDER}/zita_link_udp_ports', 'w') as f:
        d = json.dumps( zita_link_udp_ports )
        f.write(d)


def stop_zita_link():

    # SOURCES example:
    # { 'none': {},
    #   'mpd': {'jport': 'mpd_loop'},
    #   'analog': {'jport': 'system'},
    #   'remoteSalon': {'remote_delay': 0, 'ip': '192.168.1.57', 'port': 9990, 'jport': 'zita_n2j_57'}
    # }
    for source_name, params in SOURCES.items():

        if not 'remote' in source_name:
            continue

        # REMOTE
        remote_zita_restart(params["ip"], params["port"], mode='stop')

        # LOCAL
        local_zita_restart(jport=params["jport"], mode='stop')


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

    if sys.platform == 'linux' and CONFIG.get('jack'):

        # Zita network to jack (Linux)
        stop_zita_link()
        sleep(.25)

    # The server
    sp.Popen(['pkill', '-f',  'server.py paudio '])

    sleep(1)


def start():

    # Check if CamillaDPS is available
    if not check_cdsp_running():
        return

    # Run the pAudio main server 'paudio.py' to listen for commands
    srv_cmd = f'python3 {MAINFOLDER}/code/share/server.py paudio {PAUDIO_ADDR} {PAUDIO_PORT}'

    if VERBOSE:
        srv_cmd += ' -v'
    else:
        srv_cmd += f' 1>{LOGFOLDER}/paudio.log 2>{LOGFOLDER}/paudio.err'
        print("(start) The pAudio server will run in background ...")

    sp.Popen( srv_cmd.split() )

    if wait4server(timeout=20):
        if VERBOSE:
            print(f'{Fmt.BLUE}(start) pAudio server is running :-){Fmt.END}')
    else:
        print(f'{Fmt.RED}(start) No answer from `server.py paudio`, stopping all stuff.{Fmt.END}')
        stop()
        return

    if sys.platform == 'linux' and CONFIG.get('jack'):

        # Zita network to jack (Linux)
        start_zita_link()

        # Rewire CamillaDSP ONLY with Linux JACK
        rewire_camilladsp()

    # The loudness_monitor daemon
    manage_loudness_monitor_daemon()

    # Plugins (stand-alone processes)
    run_plugins()


if __name__ == "__main__":

    mode    = ''
    VERBOSE = False

    for opc in sys.argv[1:]:

        if 'start' in opc:
            mode = 'start'

        elif 'stop' in opc:
            mode = 'stop'

        elif '-j' in opc:
            mode = 'prepare_jack_stuff'

        elif '-v' in opc:
            VERBOSE = True

    match mode:

        case 'start':
            start()

        case 'stop':
            stop()


        case 'prepare_jack_stuff':
            prepare_jack_stuff()

        case _ :
            print(__doc__)
            sys.exit()
