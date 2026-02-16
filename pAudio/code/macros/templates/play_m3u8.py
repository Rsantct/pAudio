#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.
"""
    Plays an akamaized 'm3u8' playlist througby MPD

    Usage:  play_m3u8.py    station_name*  [-n]

        (*) as per configured in config/istreams.yml

        -n  disables the watchdog, see below.

    This program is a loop that feeds the m3u8 chunks into the MPD playlist.

    The loop will end:
        - if someone modifies the MPD playlist
        - if the watchdog detects a not 'radio' or 'mpd' pAudio source
"""

import  psutil
import  sys
import  os
import  yaml
import  json
import  mpd
import  m3u8
from    time import sleep
import  datetime
import  threading

UHOME = os.path.expanduser("~")

MPD_PORT        = 6600
LOG_PATH        = f'{UHOME}/pAudio/log/play_m3u8.log'
ISTREAMS_PATH   = f'{UHOME}/pAudio/istreams.yml'

# Timeout the terminate if the selected source is not 'radio' or 'mpd'
WATCHDOG_TIMEOUT = 6

mpdcli = mpd.MPDClient()

terminate_by_source = threading.Event()


def source_watchdog(timeout=60):
    """ loop that sets the terminate flag when
        a preamp source is not ~ 'radio' or ~ 'mpd'
    """

    def read_state():

        try:
            with open(f'{UHOME}/pAudio/.preamp_state', 'r') as f:
                tmp = f.read()
                return json.loads( tmp )

        except Exception as e:
            print(f'(play_m3u8) ERROR reading pAudio state: {str(e)}')
            result = {'source': 'ERROR'}

    print('starting watchdog for source changes')

    while not terminate_by_source.is_set():

        sleep(timeout)

        source = read_state().get('source', '')
        if not ('mpd' in source.lower() or 'radio' in source.lower()):
            terminate_by_source.set()


def kill_others_than_me():
    """ Kill all processes matching my basename
        except my self.
    """
    pid = os.getpid()
    my_basename = os.path.basename( __file__ )

    for proc in psutil.process_iter(['pid', 'cmdline']):

        try:
            cmdline = proc.info['cmdline']

            if proc.info['pid'] != pid and cmdline and my_basename in " ".join(cmdline):
                # terminate() -> elegant (SIGTERM); kill() -> force (SIGKILL)
                proc.kill()

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Ignore if the process disappeared on its own
            # or if we don't have permissions
            continue

        except:
            continue


def mpd_connect(port=MPD_PORT):
    try:
        mpdcli.connect('localhost', port)
        return True
    except:
        return False


def mpd_ping():

    tries = 3

    while tries:

        try:
            mpdcli.ping()
            return True
        except:
            pass

        sleep(.2)
        tries -= 1

    return False


def get_m3u8_target_duration(url):
    try:
        pl =  m3u8.load(url, timeout=5)
        return pl.target_duration
    except:
        return 0


def get_m3u8_uris(url):
    try:
        pl =  m3u8.load(url, timeout=5)
        return [x.uri for x in pl.segments]
    except:
        return []


def get_url(station_name):

    def load_istreams():
        try:
            with open(ISTREAMS_PATH, 'r') as f:
                return yaml.safe_load(f.read())
        except:
            return {}

    istreams = load_istreams()

    return istreams.get(station_name, '')


def do_log(msg, to_console=True):

    now = datetime.datetime.now()
    # ISO timestamp without microseconds:
    time_stamp = now.isoformat(timespec='seconds')

    with open(LOG_PATH, 'a') as f:
        f.write(f'{time_stamp} {msg}\n')

    if to_console:
        print(msg)


if __name__ == "__main__":


    # Kills any previous instance of this
    kill_others_than_me()

    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    # Reading the desired station
    station_name = sys.argv[1]

    # disable watchdog
    run_wd = True
    if sys.argv[2:]:
        if '-n' in sys.argv[2]:
            run_wd = False

    radio_url = get_url(station_name)

    if not radio_url:
        do_log(f"'{station_name}': not found. Bye.")
        sys.exit()

    uris = get_m3u8_uris(radio_url)

    number_of_uris = len( uris )

    if not number_of_uris:
        do_log('Error reading M3U8')
        sys.exit()

    uri_root = uris[0][: uris[0].rindex('/')]

    ts_duration = get_m3u8_target_duration( radio_url )

    if not ts_duration:
        do_log(f'{station_name}: not a valid m3u8 url. Bye.')
        sys.exit()


    # Loading the M3U8 into MPD and playing it.
    do_log(f'Loading `{station_name}` into MPD playlist')

    if not mpd_connect():
        do_log('cannot connect to MPD. Bye.')
        sys.exit()

    mpdcli.clear()
    old_consume = mpdcli.status()["consume"]
    old_random  = mpdcli.status()["random"]
    mpdcli.consume(1)
    mpdcli.random(0)


    # Source watchdog
    if run_wd:
        job_wd = threading.Thread( target=source_watchdog, args=(WATCHDOG_TIMEOUT,) )
        job_wd.start()


    # At least 2 URIs will be kept loaded in the playlist

    loop_sleep = (number_of_uris - 2) * ts_duration
    try:

        do_log(f'MPD playing `{station_name}`')

        end_reason = ''

        # Repeat every near target duration
        while True:

            play_issued = False

            # Getting the MPD playlits, and discarding the prefix `file: `
            mpd_pl = [ x.split()[-1] for x in mpdcli.playlist() ]

            # Getting the URIs, which are changing over time
            uris = get_m3u8_uris(radio_url)

            # Exit if someone wants to play anything else
            if [ uri for uri in mpd_pl if not uri_root in uri ]:
                end_reason = 'The playing queue was modified'
                break

            for uri in uris:
                if not uri in mpd_pl:
                    mpdcli.add(uri)

            if not play_issued:
                mpdcli.play()
                play_issued = True

            if not mpd_ping():
                end_reason = 'MPD connection lost'
                break

            if terminate_by_source.is_set():
                end_reason = 'selected source is not ~ \'radio\' neither ~ \'mpd\''
                break

            sleep(loop_sleep)

        if end_reason:
            do_log(f'{end_reason}')
        else:
            do_log(f'MPD playlist loop ended :-/')



    except KeyboardInterrupt:
        mpdcli.clear()
        mpdcli.consume(old_consume)
        mpdcli.random(old_random)
        do_log('\nInterrupted. Bye!')

    except Exception as e:
        do_log(f'\nException: {str(e)}')

    print('bye!')
