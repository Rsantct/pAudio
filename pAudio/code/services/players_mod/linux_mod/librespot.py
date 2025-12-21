#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" A librespot (Spotify Connect) interface module for players.py
"""

import json
import os
import sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from   common import time_sec2hhmmss

EVENTS_PATH = f'{UHOME}/pAudio/log/librespot_events'


class Fmt:
    RED     = '\033[31m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    GRAY    = '\033[90m'
    BOLD    = '\033[1m'
    END     = '\033[0m'


def _read_events():
    """ returns a list of JSON events inside EVENTS_PATH
    """

    events = []

    try:
        with open(EVENTS_PATH, 'r') as f:
            events = [json.loads(x) for x in f.read().split('\n') if x]

    except Exception as e:
        print(f'{Fmt.RED}(players_librespot) ERROR reading {os.path.basename(EVENTS_PATH)}: {str(e)}{Fmt.END}')

    return events


def get_info():

    info_void = {
        "player":       "Spotify",
        "state":        '',
        "loop_mode":    None,
        "shuffle":      None,
        "time_pos":     '',
        "time_tot":     '',
        "bitrate":      '320 Kbps',
        "artist":       '',
        "album":        '',
        "title":        '',
        "track_num":    '',
        "track_uri":    '',
        "tracks_tot":   '',
        "art_url":      '',
        "samplerate":   '44100'
    }

    info = info_void.copy()

    events = _read_events()

    try:

        for e in events[::-1]:

            if e["event"] in ('playing', 'paused'):

                if not info['state']:
                    info['state'] = e["event"]

            if e["event"] == 'repeat_changed':

                if info['loop_mode'] == None:
                    info['loop_mode'] = json.loads( e["repeat"] )

            if e["event"] == 'shuffle_changed':

                if info['shuffle'] == None:
                    info['shuffle'] = json.loads( e["shuffle"] )

            if e["event"] == 'track_changed':

                info['title']      = e.get('common_metadata_fields', {}).get('name', '')
                ms                 = e.get('common_metadata_fields', {}).get('duration_ms', '')
                info['track_uri']  = e.get('common_metadata_fields', {}).get('uri', '')
                info['art_url']    = e.get('common_metadata_fields', {}).get('covers', [])[0]
                info['track_num']  = e.get('track_metadata_fields',  {}).get('number', '')
                info['album']      = e.get('track_metadata_fields',  {}).get('album', '')
                info['artist']     = e.get('track_metadata_fields',  {}).get('artists', [])[0]
                info['time_tot']   = time_sec2hhmmss(int(ms) / 1000)

                break

    except Exception as e:
        print(f'{Fmt.RED}(players_librespot) ERROR get_current_track: {str(e)}{Fmt.END}')


    if info['title']:
        return info
    else:
        return info_void


def playback_control(*dummy):
    """ dummy """
    return 'not available'


if __name__ == "__main__":

    tmp = get_info()

    print( json.dumps(tmp) )
