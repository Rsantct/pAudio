#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" remotes sources management
"""
import  os
import  sys
import  json

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import  Fmt, read_json_file, MAINFOLDER, METATEMPLATE, \
                    send_cmd

def _init():

    global SOURCES

    pAudio_cfg = read_json_file(f'{MAINFOLDER}/.pAudio_cfg')

    SOURCES = pAudio_cfg.get('sources')


def get_meta(remoteID):

    remote = SOURCES.get(remoteID, {})
    # example:
    #  {'remote_delay': 0,
    #   'remote_track_level': True,
    #   'ip': '192.168.1.57',
    #   'port': 9990,
    #   'jport': 'zita_n2j_57'
    #  }


    if not remote:
        return METATEMPLATE.copy()

    try:
        remote_ans = send_cmd( 'player get_meta', host=remote["ip"], port=remote["port"] )
        remote_ans = json.loads( remote_ans )
        return remote_ans

    except Exception as e:
        print(f'{Fmt.RED}(remotes) ERROR getting remote metadata: {str(e)}{Fmt.END}')
        return METATEMPLATE.copy()


def playback_control(remoteID, cmd):

    remote = SOURCES.get(remoteID, {})

    try:
        remote_ans = send_cmd( f'player {cmd}', host=remote["ip"], port=remote["port"] )
        return remote_ans

    except Exception as e:
        print(f'{Fmt.RED}(remotes) ERROR remote playback: {str(e)}{Fmt.END}')
        return ''

_init()
