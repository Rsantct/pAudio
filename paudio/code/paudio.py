#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  json
import  preamp
from    miscel import *


def load_state():
    global state
    with open('../.state', 'r') as f:
        state = json.loads(f.read())
    return state


def save_state():
    with open('../.state', 'w') as f:
        f.write(json.dumps(state))


def init():
    global state
    state = load_state()
    preamp.state = state
    preamp.resume_audio_settings()


def do(cph):

    prefix, cmd, args, add = read_cmd_phrase(cph)
    result    = ''
    dosave    = True

    match prefix:

        case 'preamp':
            if cmd == 'state' or cmd.startswith('get_'):
                dosave = False
            result = preamp.do(cmd, args, add)

        case 'aux':
            if cmd == 'get_web_config':
                result = json.dumps({})

        case 'players':
            pass

        case _:
            result = 'unknown'

    if dosave:
        save_state()

    return result


# INIT
init()
