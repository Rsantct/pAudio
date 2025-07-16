#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Loudness monitor daemon

    usage:   loudness_monitor.py    start | stop
"""
import sys
import os
from subprocess import Popen
from time import sleep
import json
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

UHOME           = os.path.expanduser("~")
MAINFOLDER      = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')


PREAMP_STATE_PATH = f'{MAINFOLDER}/.preamp_state'
from common import  CONFIG, LDMON_PATH, LDCTRL_PATH
from common import  read_json_file


if CONFIG.get('coreaudio'):
    AUDIO_SOURCE = CONFIG["input"]["device"]

elif CONFIG.get('jack'):
    AUDIO_SOURCE = 'pre_in_loop'

else:
    print(f'(loudness_monitor.py) A sound server is needed. Exiting.')
    sys.exit()


def prepare_ldmon_path():
    init_values = {"LU_I": -77.0, "LU_M": -80.0, "scope": "track"}
    with open( LDMON_PATH, 'w') as f:
        f.write( json.dumps(init_values) )


def prepare_control_fifo(fname):
    try:
        if os.path.exists(fname):
            os.remove(fname)
        os.mkfifo(fname)
    except:
        print(f'(loudness_monitor.py) ERROR preparing fifo {fname}')
        raise


def control_fifo_read_loop(fname, meter):
    """ Loop forever listen for runtime commands through by the fifo control file:
        'reset'         force the reset flag to True
        'scope=xxxxx'   update the scope (metadata key observed to auto reset LU-I)
    """
    global scope
    while True:
        # opening fifo...
        with open(fname) as f:
            while True:
                f_data = f.read().strip()
                if len(f_data) == 0:
                    break

                # Resets the meter
                if f_data == 'reset':
                    meter.reset()

                # Changes the scope in runtime, i.e the
                # metadata key observed to autoreset LU-I)
                elif f_data[:6] == 'scope=':
                    new_scope = f_data[6:]
                    # validate
                    if new_scope in ('album', 'track', 'input'):
                        scope = new_scope
                        save2disk()


class My_files_event_handler(FileSystemEventHandler):
    """ A file changes handler that will reset the meter when:
        - input preamp changes
        - playing metadata album or track changes versus the scope value
    """

    def __init__(self, meter):
        self.meter            = meter  # We need to be able to reset the meter.
        self.last_album_track = ''     # Memorize last album or track

    def on_modified(self, event):

        global source, scope

        path = event.src_path

        # Check if preamp input has changed, then RESET
        if PREAMP_STATE_PATH in path:
            new_source = read_state_from_disk()['input']
            if source != new_source:
                source = new_source
                self.meter.reset()
                sleep(.25)      # anti bouncing

        # Check if metadata album or title has changed, then RESET
        if PLAYER_META_PATH in path:
            md = read_metadata_from_disk()
            if not md:
                return
            # Ignore if scope is not a metadata field name
            if not scope in ('album', 'track'):
                return
            # (i) 'track' is named 'title' in pe.audio.sys metadata fields
            md_key = scope if (scope != 'track') else 'title'
            if md[md_key] != self.last_album_track:
                self.last_album_track = md[md_key]
                self.meter.reset()
                sleep(.25)      # anti bouncing


def get_configured_scope():
    """ The configured scope ('album', 'title', '') to reset the measured LU-I.
        If void '', preamp input changes events will still reset the measure.
    """
    if 'LU_reset_scope' in CONFIG:
            scope = CONFIG['LU_reset_scope']
            # If left blank:
            if not scope:
                scope = 'input'
    else:
        # Defaults to album if not configured
        scope = 'input'

    # We accept 'track' to mean 'title'
    if scope == 'track':
        scope = 'title'
    # Check if it is a valid value
    if not ( scope in ('album', 'title', 'input') ):
        raise Exception(f'(loudness_monitor) LU_reset_scope \'{scope}\' not valid')
    return scope


def wait_M():
    """ This must be threaded.
        Call the M_event and waits for its flag to be 'set' when the meter
        has a new [M]omentary measurement change greater than a given threshold.
        Then dumps measurements to disk, and clear the M_event flag.
    """
    while True:
        meter.M_event.wait()
        save2disk()
        meter.M_event.clear()


def wait_I():
    """ This must be threaded.
        Call the I_event and waits for its flag to be 'set' when the meter
        has a new [I]ntegrated measurement change greater than a given threshold.
        Then dumps measurements to disk, and clear the M_event flag.
    """
    while True:
        meter.I_event.wait()
        save2disk()
        meter.I_event.clear()


def save2disk():
    # Saving to disk rounded to 1 dB
    with open( LDMON_PATH, 'w') as f:
        # From dBFS to dBLU ( 0 dBLU = -23dBFS )
        I_LU = meter.I - -23.0
        M_LU = meter.M - -23.0
        # Floor the value on disk as per the used threshold
        I_LU = I_LU // meter.I_threshold * meter.I_threshold
        M_LU = M_LU // meter.M_threshold * meter.M_threshold
        d = { "LU_I":  I_LU, "LU_M":  M_LU, "scope": scope }
        f.write( json.dumps(d) )


if __name__ == '__main__':

    # Reading command line: start | stop
    if sys.argv[1:]:

        if sys.argv[1] == 'stop':
            Popen( 'pkill -KILL -f "loudness_monitor.py start"', shell=True )
            with open(LDMON_PATH, 'w') as f:
                f.write('{"LU_I": -99.0, "LU_M": -99.0, "scope": "album"}')
            sys.exit()

        elif sys.argv[1] == 'start':
            # (i) Only import LU_meter when 'start' because it takes a long time,
            # so it can trouble the stop pkill (can be too much delayed).
            from audiotools.loudness_meter  import  LU_meter

        else:
            print(__doc__)
            sys.exit()
    else:
        print(__doc__)
        sys.exit()

    # Prepare LDMON_PATH file on disk
    prepare_ldmon_path()

    # Initialize the scope of the measurements (input, album or track)
    scope = get_configured_scope()

    # Initialize current preamp source
    source = read_json_file(PREAMP_STATE_PATH)['source']

    # Starts a LU_meter instance with relevant parameters:
    # M_threshold = 10.0   To avoid stress saving values to disk, because this
    #                      measure only serves as a rough signal detector.
    # I_threshold = 1.0    LU-[I]ntegrated values are relatively stable.
    meter = LU_meter( device=AUDIO_SOURCE, display=False,
                      M_threshold=10.0,
                      I_threshold=1.0 )
    meter.start()
    print(f'(loudness_monitor) getting audio from: "{AUDIO_SOURCE}"')

    # Threading the fifo listening loop for controlling this module
    prepare_control_fifo(LDCTRL_PATH)
    control = threading.Thread( target=control_fifo_read_loop,
                                args=(LDCTRL_PATH, meter) )
    control.start()

    # Threading an Observer watchdog for file changes, and passing our meter
    # instance reference in order to reset measurements if necessary.
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #  (i) Even observing recursively the CPU load is negligible
    ##observer = Observer()
    ##observer.schedule( event_handler=My_files_event_handler( meter ),
    ##                   path=MAINFOLDER, recursive=False )
    ##obsthread = threading.Thread( target=observer.start() )
    ##obsthread.start()

    # 1st writing the output file
    save2disk()

    # Threading received meter events that will trigger writing the output file
    wait_M = threading.Thread( target=wait_M )
    wait_M.start()
    wait_I = threading.Thread( target=wait_I )
    wait_I.start()
