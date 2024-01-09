#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    This is the command line pAudio launcher

        paudio.py   start [-v]  |  stop  |  toggle

            -v      verbose in attached terminal
"""

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
        print( '(i) Not found pAudio control TCP server address/port in `config.yml`,')
        print(f'    using defaults `{addr}:{port}`')

    return addr, port


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

        print(f'{Fmt.BOLD}Cannot run JACKD, exiting :-({Fmt.END}')
        sys.exit()


def start():

    # Jack audio server
    if sys.platform == 'linux' and CONFIG["sound_server"].lower() == 'jack':
        prepare_jack_stuff()

    # Control web page
    node_cmd = f'node {MAINFOLDER}/code/share/www/nodejs_www_server/www-server.js 1>/dev/null 2>&1'
    sp.Popen(node_cmd, shell=True)
    print("pAudio web server running in background ...")

    # Do audio processing and listenting for commands
    addr, port = get_srv_addr_port()
    srv_cmd = f'python3 {MAINFOLDER}/code/share/server.py paudio {addr} {port}'
    if verbose:
        srv_cmd += ' -v'
    else:
        srv_cmd += ' 1>/dev/null 2>&1'
        print("pAudio will run in background ...")
    sp.Popen(srv_cmd, shell=True)

    # Removing the CamillaDSP auto spawned Jack connections
    # and connecting pAudio `pre_in_loop` to CamillaDSP Jack port
    if sys.platform == 'linux' and CONFIG["sound_server"].lower() == 'jack':
        if wait4jackports('cpal_client_in', timeout=20):
            # (!) MUST wait a little in order to CamillaDSP Jack internal
            #     to self detect.
            sleep(1)
            jm.connect_bypattern('system', 'cpal_client_in', 'disconnect')
            jm.connect_bypattern('pre_in_loop', 'cpal_client_in', 'connect')


def restore_playback_device_settings():
    """ Only for MacOS CoreAudio """

    if sys.platform == 'darwin':

        try:
            with open(f'{MAINFOLDER}/.previous_default_device', 'r') as f:
                dev = f.read().strip()
        except:
            dev = ''

        if dev:
            print("Restoring previous Default Playback Device")
            sp.call(f'SwitchAudioSource -s "{dev}"', shell=True)
        else:
            print("Cannot read `.previous_default_device`")

        try:
            with open(f'{MAINFOLDER}/.previous_default_device_volume', 'r') as f:
                vol = f.read().strip()
        except:
            vol = ''

        if vol:
            print("Restoring previous Playback Device Volume")
            sp.call(f"osascript -e 'set volume output volume '{vol}", shell=True)
        else:
            print("Cannot read `.previous_default_device_volume`")


def stop():

    print('Stopping pAudio...')

    # camilladsp
    sp.call('pkill camilladsp', shell=True)

    # node web server
    sp.call('pkill -f "paudio\/code\/"', shell=True)

    # Jack audio server (jloops will also die)
    sp.call('pkill jackd', shell=True)
    sleep(1)
    if wait4jackports('system', timeout=.5):
        print(f'{Fmt.RED}Cannot stop JACKD{Fmt.END}')


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
