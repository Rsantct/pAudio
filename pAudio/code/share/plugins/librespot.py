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

    2025-01: librespot 0.4.0 suddently crashes, so will use a watchdog here
    2025-11: crashes stopped with libresport 0.8.0

"""
import  sys
import  os
import  subprocess as sp
from    socket import gethostname
from    getpass import getuser
import  threading
from    time import sleep


UHOME       = os.path.expanduser("~")
USER        = getuser()

try:
    BINARY = sp.check_output('which librespot'.split()).decode().strip()
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
ONEVENT_PROGRAM = os.path.dirname(__file__) + '/librespot/event_handler.py'
EVENTS_PATH     = f'{UHOME}/pAudio/log/librespot_events'

class Fmt:
    RED     = '\033[31m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    GRAY    = '\033[90m'
    BOLD    = '\033[1m'
    END     = '\033[0m'


def kill_previous(pattern):
    """ Kill previous instances as per the given process pattern
    """

    if not pattern:
        return

    current_ps = []

    try:
        current_ps = sp.check_output(['pgrep', '-f', pattern]).decode()
        current_ps = [x for x in current_ps.split('\n') if x]
    except:
        pass

    if len(current_ps) > 1:

        print(f'{Fmt.GRAY}(librespot) Killing previous `{pattern}` ...{Fmt.END}')

        for p in current_ps[:-1]:
            sp.call( f'kill -KILL {p}'.split() )


def run_watchdog(period=10):

    def check_librespot_is_running():

        with open('/dev/null', 'w') as fnull:

            # This has a reverse logic :-|
            if sp.call( ['pgrep', '-u', USER, 'librespot'], stdout=fnull, stderr=fnull ):
                return False
            else:
                return True

    while True:

        if not check_librespot_is_running():
            start()

        sleep(period)


def start():

    backend_opts = f'--backend {backend}'
    if backend == 'jackaudio':
        backend_opts += f' --device librespot'

    moreopt_str = ' '.join(OTHER_OPTS)

    cmd = f'{BINARY} --name {gethostname()} ' + \
          f'--onevent {ONEVENT_PROGRAM} ' + \
          f'--bitrate 320 {backend_opts} {moreopt_str}'

    with open('/dev/null', 'w') as f:
        sp.Popen( cmd.split(), stdout=f, stderr=f )

    print(f'{Fmt.GRAY}(librespot) running librespot ...{Fmt.END}')

    job = threading.Thread(target=run_watchdog)
    job.start()


def stop():

    print(f'{Fmt.GRAY}(librespot) stopping all stuff ...{Fmt.END}')
    kill_previous( os.path.basename(__file__) )
    sp.call( ['pkill', '-u', USER, '-KILL', '-f',  'bin/librespot']  )


if __name__ == "__main__":


    backend = 'jackaudio'
    mode = ''

    for opc in sys.argv[1:]:

        if opc == 'start':
            mode = 'start'

        elif opc == 'stop':
            mode = 'stop'

        elif 'pulse' in opc:
            backend = 'pulseaudio'

        elif 'jack' in opc:
            backend = 'jackaudio'

    if mode == 'start':
            stop()
            start()

    elif mode == 'stop':
            stop()

    else:
        print(__doc__)
        sys.exit()
