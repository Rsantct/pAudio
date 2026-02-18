#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    This plugin manages 'librespot',
    a headless Spotify Connect player daemon

    https://github.com/librespot-org/librespot

    Usage:  librespot.py   start [pulseaudio] | stop

    pulseaudio:   Uses Pulseaudio as backend instead of direct output to Jack.
                  This is useful if your pAudio sound card cannot run at the same
                  samplerate as pAudio, as mine does (ESI UDJ6 only works at 48 KHz)

    How to prepare pAudio config.yml:

        jack:
            ...
            sources:
                librespot:
                    jport:  librespot   (normal usage with Jack backend)
                         -OR-
                    jport:  PipeWire    (if you need to resample as explained above)


    2025-01: librespot 0.4.0 suddently crashes, so will use a watchdog here
    2025-11: Crashes stopped with libresport 0.8.0, but will keep the watchgog.
             Also jack ports remains stable when track changes, so the '--onevent'
             program does not need to reconnect librespot to jack anymore.

"""
import  sys
import  os
import  stat
import  subprocess as sp
import  psutil
from    socket import gethostname
from    getpass import getuser
import  threading
from    time import sleep


UHOME       = os.path.expanduser("~")
USER        = getuser()


# libresport options list (do not configure here: bitrate, name, backend, device)
OTHER_OPTS = [
    # https://github.com/librespot-org/librespot/wiki/FAQ
    # For AUDIOPHILES
    '--mixer softvol --volume-ctrl fixed --initial-volume 100',
    '--format F32 --disable-audio-cache'
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


def _init():

    global BINARY

    # Check librespot binary
    try:
        BINARY = sp.check_output('which librespot'.split()).decode().strip()
    except Exception as e:
        print(f'{Fmt.RED}(librespot) error getting librespot binary: {str(e)}{Fmt.END}')
        sys.exit()

    # Ensure +x for librespot/evenhandler.py
    try:
        curr_permissions = os.stat(ONEVENT_PROGRAM).st_mode
        # S_IXUSR (owner). Optional S_IXGRP (group) or S_IXOTH (others)
        os.chmod(ONEVENT_PROGRAM, curr_permissions | stat.S_IXUSR)
    except Exception as e:
        print(f'{Fmt.RED}(librespot) cannot chmod +x to: {ONEVENT_PROGRAM} {str(e)}{Fmt.END}')


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

    # 2025-11 spotify premium lossless 1411 kbps, but pending in librespot
    bitrate = 320

    backend_opts = f'--backend {backend}'
    if backend == 'jackaudio':
        backend_opts += f' --device librespot'

    moreopt_str = ' '.join(OTHER_OPTS)

    cmd = f'{BINARY} --name {gethostname()} ' + \
          f'--onevent {ONEVENT_PROGRAM} ' + \
          f'--bitrate {bitrate} {backend_opts} {moreopt_str}'

    with open('/dev/null', 'w') as f:
        sp.Popen( cmd.split(), stdout=f, stderr=f )

    print(f'{Fmt.GRAY}(librespot) running librespot ...{Fmt.END}')

    job = threading.Thread(target=run_watchdog)
    job.start()


def stop():

    print(f'{Fmt.GRAY}(librespot) stopping all stuff ...{Fmt.END}')
    sp.call( ['pkill', '-u', USER, '-KILL', '-f',  'bin/librespot']  )
    sp.call( ['pkill', '--older', '3', '-u', USER, '-KILL', '-f',  'librespot.py']  )


if __name__ == "__main__":

    _init()

    with open(EVENTS_PATH, 'w') as dummy:
        pass

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
