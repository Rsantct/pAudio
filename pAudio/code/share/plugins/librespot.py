#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    This plugin manages 'librespot',
    a headless Spotify Connect player daemon

    https://github.com/librespot-org/librespot

    Usage:  librespot.py   start [pulseaudio] | stop

    'pulseaudio' uses Pulseaudio as backend instead of direct output to Jack.
    This is useful if your sound card cannot run at the same samplerate as
    pe.audio.sys, as mine does (ESI UDJ6 only works at 48 KHz)

    2025-01: librespot suddently crashes, so will use a watchdog here

"""
import  sys
import  os
from    subprocess import Popen, call, check_output
from    socket import gethostname
from    getpass import getuser
import  threading
from    time import sleep

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import kill_bill, Fmt

# Current user
USER = getuser()

# librespot binary
try:
    BINARY = check_output('which librespot'.split()).decode().strip()
except Exception as e:
    print(f'{Fmt.RED}(librespot) error getting librespot binary: {str(e)}{Fmt.END}')
    sys.exit()

# libresport options list (do not configure here: bitrate, name, backend, device)
OTHER_OPTS = [
    #'--disable-audio-cache',
    # https://github.com/librespot-org/librespot/wiki/FAQ
    # For AUDIOPHILES
    '--mixer softvol --volume-ctrl fixed --initial-volume 100',
    '--format F32'
]

# Librespot --onevent program
EVENT_PROGRAM = os.path.dirname(__file__) + '/librespot/log_and_bind_ports.sh'


def run_watchdog():

    def check_librespot_is_running():

        with open('/dev/null', 'w') as fnull:

            # This has a reverse logic :-|
            if call( ['pgrep', '-u', USER, 'librespot'], stdout=fnull, stderr=fnull ):
                return False
            else:
                return True

    while True:

        if not check_librespot_is_running():
            start()

        sleep(10)


def start():

    # 'librespot' binary prints out the playing track and some info.
    # We redirect them to a temporary file that will be periodically
    # read from a player control daemon.

    BACKEND_OPTS = f'--backend {BACKEND}'
    if BACKEND == 'jackaudio':
        BACKEND_OPTS += f' --device librespot'

    moreopt_str = ' '.join(OTHER_OPTS)

    cmd = f'{BINARY} --name {gethostname()} ' + \
          f'--onevent {EVENT_PROGRAM} ' + \
          f'--bitrate 320 {BACKEND_OPTS} {moreopt_str}'

    eventsPath = f'{UHOME}/pAudio/log/.librespot_events'


    with open(eventsPath, 'a') as f:
        Popen( cmd.split(), stdout=f, stderr=f )

    print(f'{Fmt.GRAY}(librespot) running librespot ...{Fmt.END}')


    job = threading.Thread(target=run_watchdog)
    job.start()


def stop():

    print(f'{Fmt.GRAY}(librespot) stopping ...{Fmt.END}')

    # kill previous scripts like this in background
    kill_bill( os.getpid() )

    call( ['pkill', '-u', USER, '-KILL', '-f',  'bin/librespot']  )


if __name__ == "__main__":

    BACKEND = 'jackaudio'
    MODE = ''

    for opc in sys.argv[1:]:

        if opc == 'start':
            MODE = 'start'

        elif opc == 'stop':
            MODE = 'stop'

        elif 'pulse' in opc:
            BACKEND = 'pulseaudio'

        elif 'jack' in opc:
            BACKEND = 'jackaudio'

    if MODE == 'start':
            stop()
            start()

    elif MODE == 'stop':
            stop()

    else:
        print(__doc__)
        sys.exit()
