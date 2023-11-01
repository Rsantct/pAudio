#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  json
import  preamp
from    miscel import *

state = {}


def read_state_from_disk():
    global state
    with open('../.state', 'r') as f:
        state = json.loads(f.read())


def save_state():
    with open('../.state', 'w') as f:
        f.write(json.dumps(state))


def init():
    read_state_from_disk()
    # this links the 'state' variable inside preamp
    preamp.state = state
    preamp.resume_audio_settings()


def do(cph):

    prefix, cmd, args, add = read_cmd_phrase(cph)
    result    = ''
    dosave    = True

    match prefix:

        case 'preamp':
            # Some commands does not need to save the state
            if cmd == 'state' or cmd.startswith('get_'):
                dosave = False
            result = preamp.do(cmd, args, add)

        case 'aux':
            # PENDING
            if cmd == 'get_web_config':
                result = json.dumps({})

        case 'players':
            # PENDING
            pass

        case _:
            result = 'unknown'

    if dosave:
        save_state()

    return result


# INIT
init()
