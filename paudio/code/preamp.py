#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  json
import  pcamilla
from    miscel  import *
from    time    import sleep

# A link of paudio.state
state = {}

# Module propierties
INPUTS      = []
XO_SETS     = []
DRC_SETS    = []
DRCS_GAIN   = -6.0

def init():

    # Global variables
    global USER_CFG, INPUTS, DRC_SETS, XO_SETS


    # Dumping user config.yml to camillaDSP
    USER_CFG = read_user_config()
    pcamilla.set_device(USER_CFG["device"])

    INPUTS      = []
    DRC_SETS    = pcamilla.get_drc_sets()
    XO_SETS     = pcamilla.get_xo_sets()


def resume_audio_settings():
    set_level      ( state["level"] )
    set_loudness   ( state["equal_loudness"] )
    set_bass       ( state["bass"] )
    set_treble     ( state["treble"] )
    set_mute       ( state["muted"] )
    set_drc        ( state["drc_set"] )


def set_level(dB):
    return pcamilla.set_volume(dB)


def set_lu_offset():
    return ''


def set_loudness(mode):
    spl = state["level"] + 83.0
    result = pcamilla.set_loudness(mode, spl)
    return result


def set_mute(mode):
    return pcamilla.set_mute(mode)


def set_drc(name):
    # camillaDSP has not gain setting for a FIR filter,
    # so it must be done outside

    if name == 'none':
        pcamilla.set_drc_gain(DRCS_GAIN)

    res = pcamilla.set_drc(name)

    if res == 'done' and name != 'none':
        pcamilla.set_drc_gain(0.0)

    return res


def set_bass(dB):
    return pcamilla.set_bass(dB)


def set_treble(dB):
    return pcamilla.set_treble(dB)


def validate():
    return True


def do(cmd, args, add):


    def do_levels():

        # getting absolute values from relative command
        dB = x2float(args)
        if add:
            dB += state[cmd]

        if validate:

            match cmd:
                case 'level':        result = set_level(dB)
                case 'lu_offset':    result = set_lu_offset(dB)
                case 'bass':         result = set_bass(dB)
                case 'treble':       result = set_treble(dB)

        if result == 'done':
            state[cmd] = dB

        return result


    result    = 'nothing was done'

    # Some alias are accepted
    try:
        cmd = {
                'loudness':     'equal_loudness',
                'drc':          'set_drc'
        }[cmd]
    except:
        pass


    match cmd:

        case 'state':
            result = json.dumps(state)

        case 'get_inputs':
            result = json.dumps(INPUTS)

        case 'get_drc_sets':
            result = json.dumps(DRC_SETS)

        case 'get_xo_sets':
            result = json.dumps(XO_SETS)

        case 'mute':
            curr =  state['muted']
            new = switch(args, curr)
            if type(new) == bool and new != curr:
                result = set_mute(new)
            if result == 'done':
                state['muted'] = new

        case 'level' | 'lu_offset' | 'bass' | 'treble':
            result = do_levels()

        case 'equal_loudness':
            curr =  state['equal_loudness']
            new = switch(args, curr)
            if type(new) == bool and new != curr:
                result = set_loudness(new)
            if result == 'done':
                state['equal_loudness'] = new

        case 'set_drc':
            new_drc = args
            if new_drc in DRC_SETS + ['none']:
                if state["drc_set"] != new_drc:
                    result = set_drc(new_drc)
                    if result == 'done':
                        state["drc_set"] = new_drc

        case 'get_cdsp_pipeline':
            result = pcamilla.get_pipeline()

        case 'get_cdsp_config':
            result = pcamilla.get_config()

        case 'get_cdsp_drc_gain':
            result = pcamilla.get_drc_gain()

        case _:
            result = 'unknown'


    return result


init()
