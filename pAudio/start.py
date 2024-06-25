#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    This is the command line pAudio launcher

        start.py   start [-v]  |  stop  |  toggle

            -v      verbose in attached terminal
"""
#
# A helper command to check which things are running:
#
# pgrep -fla camilla; pgrep -fla node; pgrep -fla "server.py"; pgrep -fla 'plugins'
#


import  sys
import  os
from    time import sleep

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from    common import *
import  jack_mod


def get_srv_addr_port():

    addr = "localhost"
    port = 9980

    try:
        addr = CONFIG["paudio_addr"]
        port = CONFIG["paudio_port"]
    except:
        print(f'{Fmt.GRAY}(start.py) pAudio addr/port not found in`config.yml`' + \
              f' using defaults `{addr}:{port}`{Fmt.END}')

    return addr, port


def prepare_jack_stuff():
    """ execute JACK with the convenient loops
    """

    jloops = ['pre_in_loop']

    if any('mpd' in p for p in CONFIG["plugins"]):
        jloops.append('mpd_loop')


    alsa_dev = CONFIG["jack"]["device"]
    period   = CONFIG["jack"]["period"]
    nperiods = CONFIG["jack"]["nperiods"]
    fs       = CONFIG["fs"]

    if not jack_mod.run_jackd(  alsa_dev=alsa_dev,
                                fs=fs, period=period, nperiods=nperiods,
                                jloops=jloops):

        print(f'{Fmt.BOLD}(start.py) Cannot run JACKD, exiting :-({Fmt.END}')
        sys.exit()


def do_wire_dsp():
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
            print(f'{Fmt.BLUE}(start.py) set alias for camillaDSP jack ports.{Fmt.END}')
        else:
            print(f'{Fmt.BOLD}(start.py) ERROR setting alias for camillaDSP jack ports.{Fmt.END}')

        return result


    # camillaDSP jack ports aliases
    cpal_alias()

    # Removing the CamillaDSP auto spawned Jack connections
    # and connecting pAudio `pre_in_loop` to CamillaDSP Jack port
    print(f'{Fmt.GRAY}(start.py) Trying to wire camillaDSP jack ports ...{Fmt.END}')
    # (a system capture port may not exist)
    jack_mod.connect_bypattern('system',      'camilla', 'disconnect')
    jack_mod.connect_bypattern('pre_in_loop', 'camilla', 'connect'   )


def load_loudness_monitor_daemon(mode='start'):

    if mode == 'stop':
        print(f'{Fmt.GRAY}(start.py) Stopping loudness_monitor.py{Fmt.END}')

        tmp = f'python3 {MAINFOLDER}/code/share/loudness_monitor.py stop'
        sp.Popen(tmp, shell=True)

    else:
        print(f'{Fmt.GRAY}(start.py) Running loudness_monitor.py in background ...{Fmt.END}')

        tmp = f'python3 {MAINFOLDER}/code/share/loudness_monitor.py start'
        sp.Popen(tmp, shell=True)


def stop():

    print('(start.py) Stopping pAudio...')

    # The loudness_monitor daemon
    load_loudness_monitor_daemon(mode='stop')

    # Plugins (stand-alone processes)
    run_plugins(mode='stop')

    # CamillaDSP
    sp.call('pkill -KILL camilladsp', shell=True)

    # Jack audio server (jloops will also die)
    if sys.platform == 'linux' and CONFIG["sound_server"].lower() == 'jack':
        sp.call('pkill -KILL jackd', shell=True)

    # server.py (be careful with trailing space in command line below)
    sp.call('pkill -KILL -f "server\.py paudio\ "', shell=True)

    # Node.js web server
    # ---


def start():

    ADDR, PORT = get_srv_addr_port()
    CTRL_PORT  = PORT + 1

    # The stand-alone control server
    if not process_is_running('paudio_ctrl'):
        srv_cmd = f'python3 {MAINFOLDER}/code/share/server.py paudio_ctrl {ADDR} {CTRL_PORT}'
        sp.Popen(srv_cmd, shell=True)

    else:
        print(f'{Fmt.MAGENTA}(start.py) paudio_ctrl server is already running.{Fmt.END}')

    # Jack audio server
    if sys.platform == 'linux' and CONFIG["sound_server"].lower() == 'jack':
        prepare_jack_stuff()

    # Node.js control web page
    if not process_is_running('www-server'):
        node_cmd = f'node {MAINFOLDER}/code/share/www/nodejs_www_server/www-server.js 1>/dev/null 2>&1'
        sp.Popen(node_cmd, shell=True)
        print(f'{Fmt.MAGENTA}(start.py) Launching pAudio web server running in background ...{Fmt.END}')

    else:
        print(f'{Fmt.MAGENTA}(start.py) pAudio web server is already running.{Fmt.END}')

    # Run the DSP and listen for commands
    srv_cmd = f'python3 {MAINFOLDER}/code/share/server.py paudio {ADDR} {PORT}'

    if verbose:
        srv_cmd += ' -v'
    else:
        srv_cmd += ' 1>/dev/null 2>&1'
        print("(start.py) pAudio will run in background ...")

    sp.Popen(srv_cmd, shell=True)

    if not wait4server():
        print(f'{Fmt.RED}(start.py) No answer from `server.py paudio`, stopping all stuff.{Fmt.END}')
        stop()
        return

    # Wire DSP
    if sys.platform == 'linux' and CONFIG["sound_server"].lower() == 'jack':
        do_wire_dsp()

    # The loudness_monitor daemon
    load_loudness_monitor_daemon()

    # Plugins (stand-alone processes)
    run_plugins()


if __name__ == "__main__":

    verbose = False
    mode = ''

    for opc in sys.argv[1:]:

        if 'start' in opc:
            mode = 'start'

        elif 'stop' in opc:
            mode = 'stop'

        elif 'toggle' in opc:
            mode = 'toggle'

        elif '-v' in opc:
            verbose = True


    match mode:

        case 'start':
            stop()
            start()

        case 'stop':
            stop()
            restore_playback_device_settings()

        case 'toggle':
            if process_is_running(pattern='pAudio/code'):
                stop()
                restore_playback_device_settings()
            else:
                start()

        case _ :
            print(__doc__)
            sys.exit()
