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


def init():
    global state
    state = load_state()
    resume_audio_settings()


def do(cph):

    cmd, args = read_cmd_phrase(cph)
    result    = ''

    if cmd == 'state':
        result = json.dumps(state)

    elif cmd == 'level':
        dB = x2float(args)
        result = pcamilla.set_level(dB)
        if result == 'done':
            state["level"] = dB

    elif cmd == 'treble':
        dB = x2int(args)
        result = pcamilla.set_treble(dB)
        if result == 'done':
            state["treble"] = dB

    elif cmd == 'bass':
        dB = x2int(args)
        result = pcamilla.set_bass(dB)
        if result == 'done':
            state["bass"] = dB

    elif cmd == 'mute':
        mode = x2bool(args, state["muted"])
        result = pcamilla.set_mute(mode)
        if result == 'done':
            state["muted"] = mode

    elif cmd == 'loudness':
        mode = x2bool(args, state["equal_loudness"])
        result = pcamilla.set_loudness(mode)
        if result == 'done':
            state["equal_loudness"] = mode


    save_state()

    return result


# INIT
init()
