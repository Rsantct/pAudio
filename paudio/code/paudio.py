#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  subprocess as sp
from    time import sleep
import  json
import  pcamilla
from    misc import *


def load_state():
    global state
    with open('../.state', 'r') as f:
        state = json.loads(f.read())
    return state


def save_state():
    with open('../.state', 'w') as f:
        f.write(json.dumps(state))


def resume_audio_settings():
    pcamilla.set_level      (state["level"])
    pcamilla.set_loudness   (state["equal_loudness"])
    pcamilla.set_bass       (state["bass"])
    pcamilla.set_treble     (state["treble"])
    pcamilla.set_mute       (state["muted"])
    pcamilla.set_drc        (state["drc_set"])


def init():
    global state
    state = load_state()
    resume_audio_settings()


def do(cph):

    def do_levels():
        dB = x2float(args)
        if add:
            dB += state[cmd]
        result = {  'level':    pcamilla.set_level,
                    'bass':     pcamilla.set_bass,
                    'treble':   pcamilla.set_bass
                 }[cmd](dB)
        if result == 'done':
            state[cmd] = dB


    def do_booleans():
        field = {   'loudness': 'equal_loudness',
                    'mute':     'muted'
                }[cmd]
        mode = x2bool(args, state[field])
        result = {  'mute':     pcamilla.set_mute,
                    'loudness': pcamilla.set_loudness
                 }[cmd](mode)
        if result == 'done':
            state[field] = mode


    cmd, args, add = read_cmd_phrase(cph)
    result    = ''

    if cmd == 'state':
        result = json.dumps(state)

    elif cmd in ('level', 'bass', 'treble'):
        do_levels()

    elif cmd in ('mute', 'loudness'):
        do_booleans()

    elif cmd == 'drc':
        new_drc = args
        if state["drc_set"] != new_drc:
            result = pcamilla.set_drc(new_drc)
            if result == 'done':
                state["drc_set"] = new_drc

    elif cmd == 'get_pipeline':
        result = json.dumps( pcamilla.PC.get_config()["pipeline"] )


    save_state()

    return result


# INIT
init()
