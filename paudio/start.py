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

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/paudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from    common import *
import  jack_mod as jm


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


def restore_playback_device_settings():
    """ Only for MacOS CoreAudio """

    if sys.platform == 'darwin':

        try:
            with open(f'{MAINFOLDER}/.previous_default_device', 'r') as f:
                dev = f.read().strip()
        except:
            dev = ''

        if dev:
            print("(start.py) Restoring previous Default Playback Device")
            sp.call(f'SwitchAudioSource -s "{dev}"', shell=True)
        else:
            print("(start.py) Cannot read `.previous_default_device`")

        try:
            with open(f'{MAINFOLDER}/.previous_default_device_volume', 'r') as f:
                vol = f.read().strip()
        except:
            vol = ''

        if vol:
            print("(start.py) Restoring previous Playback Device Volume")
            sp.call(f"osascript -e 'set volume output volume '{vol}", shell=True)
        else:
            print("(start.py) Cannot read `.previous_default_device_volume`")


# *** WORK IN PROGRESS ***
def prepare_jack_stuff():
    """ *** WORK IN PROGRESS ***
    """

    alsa_dev = 'hw:U192k'
    fs       = CONFIG["fs"]
    period   = 2048
    nperiods = 3

    if not jm.run_jackd( alsa_dev=alsa_dev,
                         fs=fs,
                         period=period, nperiods=nperiods,
                         jloops=['pre_in_loop']):

        print(f'{Fmt.BOLD}(start.py) Cannot run JACKD, exiting :-({Fmt.END}')
        sys.exit()


def start():

    ADDR, PORT = get_srv_addr_port()
    CTRL_PORT  = PORT + 1

    # The stand-alone control server
    if not process_is_running('paudio_ctrl'):
        srv_cmd = f'python3 {MAINFOLDER}/code/share/server.py paudio_ctrl {ADDR} {CTRL_PORT}'
        sp.Popen(srv_cmd, shell=True)
    else:
        print(f'{Fmt.MAGENTA}(restart.py) paudio_ctrl server is already running.{Fmt.END}')

    # Jack audio server
    if sys.platform == 'linux' and CONFIG["sound_server"].lower() == 'jack':
        prepare_jack_stuff()

    # Node.js control web page
    if not process_is_running('www-server'):
        node_cmd = f'node {MAINFOLDER}/code/share/www/nodejs_www_server/www-server.js 1>/dev/null 2>&1'
        sp.Popen(node_cmd, shell=True)
        print(f'{Fmt.MAGENTA}(restart.py) pAudio web server running in background ...{Fmt.END}')
    else:
        print(f'{Fmt.MAGENTA}(restart.py) pAudio web server is already running.{Fmt.END}')

    # Do audio processing and listenting for commands
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
        sys.exit()

    # Plugins (stand-alone processes)
    run_plugins()

    # Removing the CamillaDSP auto spawned Jack connections
    # and connecting pAudio `pre_in_loop` to CamillaDSP Jack port
    if sys.platform == 'linux' and CONFIG["sound_server"].lower() == 'jack':
        if wait4jackports('cpal_client_in', timeout=20):
            # (!) MUST wait a little in order to CamillaDSP Jack internal
            #     to self detect.
            sleep(1)
            jm.connect_bypattern('system', 'cpal_client_in', 'disconnect')
            jm.connect_bypattern('pre_in_loop', 'cpal_client_in', 'connect')


def stop():

    print('(start.py) Stopping pAudio...')

    # Plugins (stand-alone processes)
    run_plugins('stop')

    # Jack audio server (jloops will also die)
    if sys.platform == 'linux' and CONFIG["sound_server"].lower() == 'jack':
        sp.call('pkill -KILL jackd', shell=True)
        sleep(1)
        if wait4jackports('system', timeout=.5):
            print(f'{Fmt.RED}(start.py) Cannot stop JACKD{Fmt.END}')

    # CamillaDSP
    sp.call('pkill -KILL camilladsp', shell=True)

    # server.py (be careful with trailing space in command line below)
    sp.call('pkill -KILL -f "server\.py paudio\ "', shell=True)


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
            if process_is_running(pattern='paudio/code'):
                stop()
                restore_playback_device_settings()
            else:
                start()

        case _ :
            print(__doc__)
            sys.exit()
