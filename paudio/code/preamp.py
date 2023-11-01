#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  subprocess as sp
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
DRCS_GAIN   = -6.0  # By now we assume a constant DRC gain for any drc FIR


def init():

    # Global variables
    global CONFIG, INPUTS, DRC_SETS, XO_SETS

    CONFIG      = read_user_config()
    INPUTS      = []
    DRC_SETS    = get_drc_sets_from_loudspeaker(CONFIG["loudspeaker"])
    XO_SETS     = pcamilla.get_xo_sets()

    # Dumping user configs to camillaDSP
    pcamilla.init_camilladsp(user_config=CONFIG, drc_sets=DRC_SETS)


def resume_audio_settings():
    do_levels( 'level',  state["level"]     )
    do_levels( 'bass',   state["bass"]      )
    do_levels( 'treble', state["treble"]    )
    set_mute(            state["muted"]     )
    set_drc(             state["drc_set"]   )


def set_mute(mode):
    return pcamilla.set_mute(mode)


def set_loudness(mode, level):
    spl = level + 83.0
    result = pcamilla.set_loudness(mode, spl)
    return result


def set_drc(drcID):
    # camillaDSP has not gain setting for a FIR filter,
    # so it must be done outside

    if drcID == 'none':
        pcamilla.set_drc_gain(DRCS_GAIN)

    res = pcamilla.set_drc(drcID)

    if res == 'done' and drcID != 'none':
        pcamilla.set_drc_gain(0.0)

    return res


def do_levels(cmd, dB, add=False):
    """ Level related commands """

    def set_level(dB):
        pcamilla.set_volume(dB)
        return set_loudness(state["equal_loudness"], dB)


    def set_lu_offset(dB):
        return pcamilla.set_lu_offset(-dB)


    def set_bass(dB):
        return pcamilla.set_bass(dB)


    def set_treble(dB):
        return pcamilla.set_treble(dB)


    def headroom():
        hr = 0
        return hr


    # getting absolute values from relative command
    dB = x2float(dB)
    if add:
        dB += state[cmd]

    if headroom() >= 0:
        match cmd:
            case 'level':        result = set_level(dB)
            case 'lu_offset':    result = set_lu_offset(dB)
            case 'bass':         result = set_bass(dB)
            case 'treble':       result = set_treble(dB)

    else:
        result = 'no headroom'

    if result == 'done':
        state[cmd] = dB

    return result


def normalize_cmd(cmd):
    """ Some alias are accepted for some commands """
    try:
        cmd = {
                'loudness':     'equal_loudness',
                'drc':          'set_drc'
        }[cmd]
    except:
        pass
    return cmd


def do(cmd, args, add):

    cmd     = normalize_cmd(cmd)
    result  = 'nothing was done'

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

        case 'equal_loudness':
            curr_mode =  state['equal_loudness']
            new_mode = switch(args, curr_mode)
            if type(new_mode) == bool and new_mode != curr_mode:
                result = set_loudness(new_mode, state["level"])
            if result == 'done':
                state['equal_loudness'] = new_mode

        case 'set_drc':
            new_drc = args
            if new_drc in DRC_SETS + ['none']:
                if state["drc_set"] != new_drc:
                    result = set_drc(new_drc)
                    if result == 'done':
                        state["drc_set"] = new_drc

        # Level related commands
        case 'level' | 'lu_offset' | 'bass' | 'treble':
            result = do_levels(cmd, args, add)

        # Special commands when using cammillaDSP
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
