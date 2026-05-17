#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    shairport-sync  Plays audio streamed from AirPlay sources.

    Usage:    shairport-sync.py   start | stop
"""
import  sys
import  os
import  subprocess  as sp
from    socket      import gethostname
from    getpass     import getuser
import  threading
from    time        import sleep

#
# NOTICE:
#
#   - shairport-sync NEEDS Jack at 44100
#
#   - Debian package system service NEEDS to be disabled after installing:
#       sudo systemctl stop shairport-sync.service
#       sudo systemctl disable shairport-sync.service
#
#    - While processing audio, shairport-sync spend high CPU %
#

UHOME = os.path.expanduser("~")
USER  = getuser()


class Fmt:
    RED     = '\033[31m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    GRAY    = '\033[90m'
    BOLD    = '\033[1m'
    END     = '\033[0m'


def run_watchdog():

    def check_if_running():

        with open('/dev/null', 'w') as fnull:

            # This has a reverse logic :-|
            if sp.call( ['pgrep', '-u', USER, 'shairport-sync'], stdout=fnull, stderr=fnull ):
                return False
            else:
                return True

    while True:

        if not check_if_running():
            start()

        sleep(10)


def start():

    log_path = f'{UHOME}/pAudio/log/shairport-sync.log'

    # Former versions used alsa but recent debian package alows jack :-)
    cmdlist = ['shairport-sync',  '-a', gethostname(), '-o' , 'jack']

    with open(log_path, 'w') as f:
        sp.Popen( cmdlist, stdout=f, stderr=f )

    job = threading.Thread(target=run_watchdog)
    job.start()


def stop():

    # kill previous scripts like this in background
    print(f'{Fmt.GRAY}(shairport-sync) stopping all stuff ...{Fmt.END}')
    sp.call( ['pkill', '-u', USER, '-KILL', '-f',  'bin/shairport-sync']  )
    sp.call( ['pkill', '--older', '3', '-u', USER, '-KILL', '-f',  'shairport-sync']  )


if __name__ == "__main__":

    if sys.argv[1:]:

        if sys.argv[1] == 'start':
            stop()
            start()

        elif sys.argv[1] == 'stop':
            stop()

        else:
            print(__doc__)


    else:
        print(__doc__)
