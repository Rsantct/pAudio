#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    This is the command line pAudio launcher

        start.py   start [-v]  |  stop  |  toggle

            -v      verbose in attached terminal
"""
#
# A helper command to check what things are running:
#
# pgrep -fla camilla; pgrep -fla node; pgrep -fla "server.py"; pgrep -fla 'plugins'
#


import  sys
import  os
from    time import sleep

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')
sys.path.append(f'{MAINFOLDER}/code/services/preamp_mod')

from    common  import *

# import Jack stuff ONLY with LINUX
if sys.platform == 'linux' and CONFIG.get('jack'):
    import  jack_mod
    from    jack_sources import SOURCES


def prepare_jack_stuff():
    """ execute JACK with the convenient loops
    """

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
            print(f'{Fmt.BLUE}(start) Reloading PipeWire for jack-sink ...{Fmt.END}')

        except Exception as e:
            print(f'{Fmt.BOLD}(start) Problems restarting PipeWire: {str(e)}{Fmt.END}')


def rewire_dsp():
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
            print(f'{Fmt.BLUE}(start) set alias for camillaDSP jack ports.{Fmt.END}')
        else:
            print(f'{Fmt.BOLD}(start) ERROR setting alias for camillaDSP jack ports.{Fmt.END}')

        return result


    # camillaDSP jack ports aliases
    cpal_alias()

    # Removing the CamillaDSP auto spawned Jack connections
    # and connecting pAudio `pre_in_loop` to CamillaDSP Jack port
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
            print(f'{Fmt.BLUE}{Fmt.BOLD}Running plugin: {plugin} ...{Fmt.END}')
            sp.Popen(f'{PLUGINSFOLDER}/{plugin} start', shell=True)

    elif mode == 'stop':
        for plugin in CONFIG["plugins"]:
            print(f'{Fmt.GRAY}Stopping plugin: {plugin} ...{Fmt.END}')
            sp.Popen(f'{PLUGINSFOLDER}/{plugin} stop', shell=True)


def manage_loudness_monitor_daemon(mode='start'):

    if mode == 'stop':

        if not process_is_running('loudness_monitor.py'):
            return()

        print(f'{Fmt.GRAY}(start) Stopping loudness_monitor.py{Fmt.END}')

        tmp = f'python3 {MAINFOLDER}/code/share/loudness_monitor.py stop'
        sp.call(tmp, shell=True)

    else:
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

        print( f'(start) Running zita-njbridge for: `{ source_name }`' )

        # Trying to RUN THE REMOTE SENDER zita-j2n (**)
        print(f'{Fmt.GRAY}(start) starting remote zita-j2n at: {params["ip"]}{Fmt.END}')
        remote_zita_restart(params["ip"], params["port"], UDP_PORT)

        # Append the UPD_PORT to zita_link_udp_ports
        zita_link_udp_ports[source_name] = { 'addr':    params["ip"],
                                             'port':    params["port"],
                                             'udpport': UDP_PORT}

        # RUN LOCAL RECEIVER:
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

    print(f'{Fmt.GRAY}{Fmt.BOLD}(start) Stopping pAudio{Fmt.END}')

    # Only macOS
    if sys.platform == 'darwin':
        macos.restore_playback_device()

    # The loudness_monitor daemon
    manage_loudness_monitor_daemon(mode='stop')

    # Plugins (stand-alone processes)
    run_plugins(mode='stop')

    if not only_server:

        # CamillaDSP
        sp.call('pkill -KILL camilladsp', shell=True)

        # Jack audio server (jloops will also die)
        if sys.platform == 'linux' and CONFIG.get('jack'):

            # Stop Zita_Link
            stop_zita_link()
            sleep(.25)

            # Stop Jack
            sp.call('pkill -KILL jackd', shell=True)

    # server.py (be careful with trailing space in command line below)
    sp.call('pkill -KILL -f "server.py paudio "', shell=True)

    # Node.js web server
    # ---


def start():


    # The stand-alone control server
    if not process_is_running('paudio_ctrl'):
        CTRL_PORT = PAUDIO_PORT + 1
        srv_cmd = f'python3 {MAINFOLDER}/code/share/server.py paudio_ctrl {PAUDIO_ADDR} {CTRL_PORT}'
        sp.Popen(srv_cmd, shell=True)

    else:
        print(f'{Fmt.GREEN}(start) paudio_ctrl server is already running.{Fmt.END}')

    # Node.js control web page
    if not process_is_running('www-server'):
        node_cmd = f'node {MAINFOLDER}/code/share/www/nodejs_www_server/www-server.js 1>/dev/null 2>&1'
        sp.Popen(node_cmd, shell=True)
        print(f'{Fmt.MAGENTA}(start) Launching pAudio web server running in background ...{Fmt.END}')

    else:
        print(f'{Fmt.GREEN}(start) pAudio web server is already running.{Fmt.END}')


    if not only_server:
        # Jack audio server
        if sys.platform == 'linux' and CONFIG.get('jack'):

            # Jack
            prepare_jack_stuff()

            # remote sources
            start_zita_link()


    # Special flag file for 'paudio.py'.
    with open(f'{MAINFOLDER}/.paudio_flags', 'w') as f:
        if only_server:
            paudio_flags = {'run_camilladsp': False}
        else:
            paudio_flags = {'run_camilladsp': True}
        f.write( json.dumps(paudio_flags) )

    # Run the pAudio main server 'paudio.py' to listen for commands
    # This INCLUDES running CamillaDSP with a proper configuration.
    srv_cmd = f'python3 {MAINFOLDER}/code/share/server.py paudio {PAUDIO_ADDR} {PAUDIO_PORT}'

    if verbose:
        srv_cmd += ' -v'
    else:
        srv_cmd += f' 1>{LOGFOLDER}/paudio.log 2>{LOGFOLDER}/paudio.err'
        print("(start) pAudio will run in background ...")

    sp.Popen(srv_cmd, shell=True)

    if not wait4server():
        print(f'{Fmt.RED}(start) No answer from `server.py paudio`, stopping all stuff.{Fmt.END}')
        stop()
        return


    if not only_server:

        # Rewire CamillaDSP ONLY with JACK
        if sys.platform == 'linux' and CONFIG.get('jack'):
            rewire_dsp()

        # The loudness_monitor daemon
        manage_loudness_monitor_daemon()

        # Plugins (stand-alone processes)
        run_plugins()


if __name__ == "__main__":

    verbose     = False
    only_server = False
    mode        = ''

    for opc in sys.argv[1:]:

        if 'start' in opc:
            mode = 'start'

        elif 'stop' in opc:
            mode = 'stop'

        elif 'toggle' in opc:
            mode = 'toggle'

        elif '-v' in opc:
            verbose = True


        elif '-s' in opc:
            only_server = True


    match mode:

        case 'start':
            stop()
            print(f'{Fmt.GRAY}{Fmt.BOLD}wait a bit to start pAudio... .. .{Fmt.END}')
            sleep(3)
            start()

        case 'stop':
            stop()

        case 'toggle':
            if process_is_running(pattern='pAudio/code'):
                stop()
            else:
                start()

        case _ :
            print(__doc__)
            sys.exit()
