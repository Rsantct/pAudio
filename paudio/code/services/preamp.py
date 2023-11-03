#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Preamp subsystem.
    Version with CamillaDSP processor (https://github.com/HEnquist/camilladsp)
"""

import  subprocess as sp
import  json
from    time    import sleep

from    common  import *

THIS_DIR = os.path.dirname(__file__)
sys.path.append(f'{THIS_DIR}/preamp_mod')

import  pcamilla as DSP

# Main variable (preamplifier state)
state = {}


# Constants
STATE_PATH  = f'{MAINFOLDER}/.preamp_state'
INPUTS      = []
TARGET_SETS = []
XO_SETS     = []
DRC_SETS    = []
DRCS_GAIN   = -6.0  # By now we assume a constant DRC gain for any drc FIR


def init():

    global state, INPUTS, TARGET_SETS, DRC_SETS, XO_SETS

    state = read_json_file(STATE_PATH)


    INPUTS      = CONFIG["inputs"]
    TARGET_SETS = get_target_sets(fs=CONFIG["fs"])
    DRC_SETS    = get_drc_sets_from_loudspeaker(CONFIG["loudspeaker"])
    XO_SETS     # PENDING

    # Optional user config having precedence over the saved state:
    if "room_target" in CONFIG:
        if not CONFIG["room_target"] in TARGET_SETS + ['none']:
            CONFIG["room_target"] = 'none'
            print(f'{Fmt.BOLD}ERROR in config room_target{Fmt.END}')
    else:
        CONFIG["room_target"] = state["target"]


    # State FS is just informative
    state["fs"] = CONFIG["fs"]

    # Running camillaDSP
    DSP.init_camilladsp(user_config=CONFIG, drc_sets=DRC_SETS)

    # Resuming audio settings
    do_levels( 'level',         state["level"]     ,    update_state=False)
    do_levels( 'lu_offset',     state["lu_offset"] ,    update_state=False)
    do_levels( 'bass',          state["bass"]      ,    update_state=False)
    do_levels( 'treble',        state["treble"]    ,    update_state=False)
    do_levels( 'target',        CONFIG["room_target"],  update_state=True)
    set_mute(                   state["muted"]     )
    set_drc(                    state["drc_set"]   )
    set_xo(                     state["xo_set"]    )


def set_mute(mode):
    return DSP.set_mute(mode)


def set_loudness(mode, level):
    spl = level + 83.0
    result = DSP.set_loudness(mode, spl)
    return result


def set_drc(drcID):
    # camillaDSP has not gain setting for a FIR filter,
    # so it must be done outside

    if drcID == 'none':
        DSP.set_drc_gain(DRCS_GAIN)

    res = DSP.set_drc(drcID)

    if res == 'done' and drcID != 'none':
        DSP.set_drc_gain(0.0)

    return res


def set_xo(xoID):
    return DSP.set_xo(xoID)


def do_levels(cmd, dB, add=False, update_state=True):
    """ Level related commands """

    def set_level(dB):
        DSP.set_volume(dB)
        return set_loudness(state["equal_loudness"], dB)


    def set_lu_offset(dB):
        return DSP.set_lu_offset(-dB)


    def set_bass(dB):
        return DSP.set_bass(dB)


    def set_treble(dB):
        return DSP.set_treble(dB)


    def set_target(tID):
        return DSP.set_target(tID)


    def headroom():

        sc = state.copy()
        sc[cmd] = dB

        hr = - sc["level"] + sc["lu_offset"] + DRCS_GAIN

        if sc["bass"]   and not sc["tone_defeat"] > 0:
            hr -= sc["bass"]

        if sc["treble"] and not sc["tone_defeat"] > 0:
            hr -= sc["treble"]

        if sc["target"] != 'none':
            tgain = x2float( sc["target"][:4] )
            if tgain > 0:
                hr -= tgain

        return hr


    try:
        dB = x2float(dB)
    except:
        tID = dB

    # getting absolute values from relative command
    if add:
        dB += state[cmd]

    if headroom() >= 0:

        match cmd:
            case 'level':        result = set_level(dB)
            case 'lu_offset':    result = set_lu_offset(dB)
            case 'bass':         result = set_bass(dB)
            case 'treble':       result = set_treble(dB)
            case 'target':       result = set_target(tID)

    else:
        result = 'no headroom'

    if result == 'done' and update_state:
        if cmd == 'target':
            state[cmd] = tID
        else:
            state[cmd] = dB

    return result


def normalize_cmd(cmd):
    """ Some alias are accepted for some commands """
    try:
        cmd = {
                'loudness':     'equal_loudness',
                'set_target':   'target',
                'drc':          'set_drc',
                'xo':           'set_xo'
        }[cmd]
    except:
        pass
    return cmd


def do(cmd, args, add):

    cmd     = normalize_cmd(cmd)
    result  = 'nothing was done'

    if cmd == 'state' or cmd.startswith('get_'):
        dosave = False
    else:
        dosave = True

    match cmd:

        case 'state':
            result = json.dumps(state)

        case 'get_inputs':
            result = json.dumps(INPUTS)

        case 'get_target_sets':
            result = json.dumps(TARGET_SETS)

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

        case 'set_xo':
            new_xo = args
            if new_xo in XO_SETS + ['none']:
                if state["xo_set"] != new_xo:
                    result = set_xo(new_xo)
                    if result == 'done':
                        state["xo_set"] = new_xo

        # Level related commands
        case 'level' | 'lu_offset' | 'bass' | 'treble':
            result = do_levels(cmd, args, add)

        case 'target':
            newt = args
            if newt in TARGET_SETS + ['none']:
                if state["target"] != newt:
                    result = do_levels('target', newt)
                    if result == 'done':
                        state["target"] = newt

        # Special commands when using cammillaDSP
        case 'get_cdsp_pipeline':
            result = DSP.get_pipeline()

        case 'get_cdsp_config':
            result = DSP.get_config()

        case 'get_cdsp_drc_gain':
            result = DSP.get_drc_gain()

        case _:
            result = 'unknown command'

    if dosave:
        save_json_file(state, STATE_PATH)

    return result


init()
