#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  json
import  pcamilla
from    miscel import *

state = {}


def resume_audio_settings():
    pcamilla.set_level      (state["level"])
    pcamilla.set_loudness   (state["equal_loudness"])
    pcamilla.set_bass       (state["bass"])
    pcamilla.set_treble     (state["treble"])
    pcamilla.set_mute       (state["muted"])
    pcamilla.set_drc        (state["drc_set"])


def do(cmd, args, add):


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
        return result


    def do_booleans():

        # map        command        -->  state field
        field = {   'loudness':         'equal_loudness',
                    'equal_loudness':   'equal_loudness',
                    'mute':             'muted'
                }[cmd]

        # new mode as per the current one
        new_mode = x2bool(args, state[field])

        result = {  'mute':             pcamilla.set_mute,
                    'loudness':         pcamilla.set_loudness,
                    'equal_loudness':   pcamilla.set_loudness
                 }[cmd](new_mode)

        if result == 'done':
            state[field] = new_mode

        return result


    result    = ''

    match cmd:

        case 'state':
            result = json.dumps(state)

        case 'get_inputs':
            result = json.dumps(pcamilla.get_inputs())

        case 'get_drc_sets':
            result = json.dumps(pcamilla.get_drc_sets())

        case 'get_xo_sets':
            result = json.dumps(pcamilla.get_xo_sets())

        case 'level' | 'bass' | 'treble':
            result = do_levels()

        case 'mute' | 'loudness' | 'equal_loudness':
            result = do_booleans()

        case 'drc' | 'set_drc':
            new_drc = args
            if state["drc_set"] != new_drc:
                result = pcamilla.set_drc(new_drc)
                if result == 'done':
                    state["drc_set"] = new_drc
            else:
                result = 'nothing done'

        case 'get_pipeline':
            result = json.dumps( pcamilla.PC.get_config()["pipeline"] )

        case _:
            result = 'unknown'


    return result

