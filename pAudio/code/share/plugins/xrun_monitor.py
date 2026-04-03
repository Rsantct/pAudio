#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" A monitor for PipeWire or Jack XRUNS

    For Pipewire, will poll periodically 'pw-top' utility

    For Jack, will set a python-jack callback

    Usage:  xrun_monitor.py [path/to/file.log] start|stop

        (log file is optional)
"""

import  sys
import  subprocess  as sp
import  threading
from    time        import sleep
from    datetime    import datetime
import  jack
from    getpass     import getuser


# CONFIGURE HERE THE PIPEWIRE NODE/DEVICE NAMES TO BE MONITORED
# (case insensitive)
PWTOP_WANTED = ['jack_sink', 'spotify', 'librespot']
PWTOP_PERIOD = 1


def get_timestamp():
    """ the timestamp string, example: '2025-01-02T08:58:59'
    """
    return datetime.now().isoformat(timespec='seconds')


def get_pw_top_errors():
    """
        returns a list of wanted pw nodes with errors, example:

        [('jack_sink', 0), ('librespot', 0)]
    """

    res = []

    try:
        tmp = sp.check_output('pw-top -b -n2'.split()).decode()

        # S   ID  QUANT   RATE    WAIT    BUSY   W/Q   B/Q  ERR FORMAT           NAME
        # C   31      0      0    ---     ---   ---   ---     0                  Dummy-Driver
        # C   32      0      0    ---     ---   ---   ---     0                  Freewheel-Driver
        # C   38      0      0    ---     ---   ---   ---     0                  jack_sink
        # C   42      0      0    ---     ---   ---   ---     0                  Midi-Bridge
        # C   53      0      0    ---     ---   ---   ---     0                  spotify
        # S   ID  QUANT   RATE    WAIT    BUSY   W/Q   B/Q  ERR FORMAT           NAME
        # S   31      0      0    ---     ---   ---   ---     0                  Dummy-Driver
        # S   32      0      0    ---     ---   ---   ---     0                  Freewheel-Driver
        # R   38    512  44100  60,7us  10,1us  0,01  0,00    0     F32P 2 44100 jack_sink
        # R   53   8192  44100  24,8us  22,2us  0,00  0,00    0    F32LE 2 44100  + spotify
        # S   42      0      0    ---     ---   ---   ---     0                  Midi-Bridge

    except:
        return res

    lines = tmp.split('\n')
    lines = [x.strip() for x in lines]

    for line in lines:

        if 'W/Q' in line and 'B/Q' in line:
            res = []

        for w in PWTOP_WANTED:

            if w in line.lower():

                line_chunks = line.split()

                err = int(line_chunks[8])

                res.append( (w, err) )

    return res


def do_pw_top_loop():
    """ a loop to be threaded that monitorizes pw errors
    """

    while True:


        # list
        errors = get_pw_top_errors()

        if not errors:
            do_log('PIPEWIRE pw-top NOT RESPONDING')

        else:
            tmp = ''
            for node, nerr in errors:
                if nerr > 0:
                    tmp += f' {node}:{n},'
            if tmp:
                tmp = f'pw-top XRUNS:{tmp}'[:-1]
                do_log(tmp)

        sleep(PWTOP_PERIOD)


def pw_is_running():

    try:
        sp.check_output('pgrep pipewire'.split())
        return True
    except:
        return False


def jack_xrun_handler(x):

    tmp = f'jackd XRUNS: {str(x)}'
    do_log(tmp)


def do_log(msg, mode='a'):

    if LOGPATH:
        with open(LOGPATH, mode) as f:
            f.write(f'{get_timestamp()} {msg}\n')
    else:
        print(f'{get_timestamp()} {msg}')


def stop():
    do_log('stopping')
    sp.call( ['pkill', '--older', '3', '-u', getuser(), '-KILL', '-f',  'paudio_xrun_monitor.py']  )


def start():

    do_log('paudio_xrun_monitor started', mode='w')

    # Pipewire monitoring if detected
    if pw_is_running():
        pw_top_job = threading.Thread(target=do_pw_top_loop)
        pw_top_job.start()
        do_log('waiting for xruns in both pw-top or jackd ...')
    else:
        do_log('waiting for xruns in jackd ...')


    # Jack monitoring
    jcli = jack.Client('tmp', no_start_server=True)
    jcli.set_xrun_callback(jack_xrun_handler)

    with jcli:
        jcli.activate()

        try:
            while True:
                sleep(1)

        except KeyboardInterrupt:
            print("Exiting Jack client...")

        finally:
            jcli.deactivate()
            jcli.close()
            print("Jack client exited.")


if __name__ == "__main__":

    LOGPATH = ''
    mode = ''

    for opc in sys.argv[1:]:

        if '-h' in opc:
            print(__doc__)
            sys.exit()

        elif opc == 'start' or  opc == 'stop':
            mode = opc

        else:
            LOGPATH = sys.argv[1]

    if mode == 'stop':
        stop()

    elif mode == 'start':
        stop()
        sleep(1)
        start()

    else:
        print(__doc__)
