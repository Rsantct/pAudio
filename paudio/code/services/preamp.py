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

# Constants
STATE_PATH  = f'{MAINFOLDER}/.preamp_state'
INPUTS      = []
TARGET_SETS = []
XO_SETS     = []
DRC_SETS    = []
# By now we assume a constant DRC gain for any provided drc.X.XXX FIR file
DRCS_GAIN   = -6.0


# Main variable (preamplifier state)
state = read_json_file(STATE_PATH)


def init():

    global state, INPUTS, TARGET_SETS, DRC_SETS, XO_SETS

    INPUTS      = CONFIG["inputs"]
    TARGET_SETS = get_target_sets(fs=CONFIG["fs"])
    DRC_SETS    = get_drc_sets_from_loudspeaker(CONFIG["loudspeaker"])
    XO_SETS     # PENDING


    # State FS is just informative
    state["fs"] = CONFIG["fs"]

    # Optional user configs having precedence over the saved state:
    for prop in 'bass', 'treble', 'lu_offset', 'target', 'equal_loudness', 'drc_set':
        if prop in CONFIG:
            match prop:
                case 'drc_set':
                    if CONFIG["drc_set"] in DRC_SETS + ['none']:
                        state["drc_set"] = CONFIG["drc_set"]
                    else:
                        print(f'{Fmt.BOLD}ERROR in config drc_set{Fmt.END}')
                case 'target':
                    if CONFIG["target"] in TARGET_SETS + ['none']:
                        state["target"] = CONFIG["target"]
                    else:
                        print(f'{Fmt.BOLD}ERROR in config target{Fmt.END}')
                case _:
                    state[prop] = CONFIG[prop]


    # Preparing and running camillaDSP
    DSP.init_camilladsp(user_config=CONFIG, drc_sets=DRC_SETS)


    # Resuming audio settings

    do_levels( 'level', dB=state["level"] )
    set_mute( state["muted"] )

    # Resuming audio settings can be user configured ones

    # tones can be clamped when ordered out of range
    result = do_levels( 'bass', dB=state["bass"] )
    if result != 'done':
        print(f'{Fmt.BOLD}{result}{Fmt.END}')
        state["bass"] = x2float(result.split()[-1])

    result = do_levels( 'treble', dB=state["treble"] )
    if result != 'done':
        print(f'{Fmt.BOLD}{result}{Fmt.END}')
        state["treble"] = x2float(result.split()[-1])

    do_levels( 'lu_offset', dB=state["lu_offset"] )

    do_levels( 'target', tID=state["target"] )

    set_loudness( mode=state["equal_loudness"] )

    set_drc( state["drc_set"] )

    # XO is pending
    #set_xo( state["xo_set"] )

    # Saving state with user settings
    save_json_file(state, STATE_PATH)

    return


def set_mute(mode):
    return DSP.set_mute(mode)


def set_loudness(mode, level=state["level"]):
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


def set_input(inputID):
    return "done"


def do_levels(cmd, dB=0.0, tID='+0.0-0.0', tone_defeat='False', add=False):
    """ Level related commands
    """

    def set_level(dB):
        DSP.set_volume(dB)
        return set_loudness(mode=state["equal_loudness"], level=dB)


    def set_lu_offset(dB):
        return DSP.set_lu_offset(-dB)


    def set_bass(dB):
        if not state["tone_defeat"]:
            return DSP.set_bass(dB)
        else:
            return "done"


    def set_treble(dB):
        if not state["tone_defeat"]:
            return DSP.set_treble(dB)
        else:
            return "done"


    def set_target(tID):
        return DSP.set_target(tID)


    def set_tone_defeat(mode):
        res = []
        if mode == True:
            res.append( DSP.set_bass(   0.0 ) )
            res.append( DSP.set_treble( 0.0 ) )
        else:
            res.append( DSP.set_bass(   state["bass"]   ) )
            res.append( DSP.set_treble( state["treble"] ) )
        res = ' '.join( set(res) )
        return res


    def calc_headroom():

        candidate = state.copy()

        if cmd == 'target':
            candidate['target'] = tID
        else:
            candidate[cmd] = dB

        hr = - candidate["level"] + candidate["lu_offset"] + DRCS_GAIN

        if candidate["bass"] > 0   and not candidate["tone_defeat"]:
            hr -= candidate["bass"]

        if candidate["treble"] > 0 and not candidate["tone_defeat"]:
            hr -= candidate["treble"]

        if candidate["target"] != 'none':
            tgain = x2float( candidate["target"][:4] )
            if tgain > 0:
                hr -= tgain

        return hr


    # getting absolute values from relative command
    if add:
        dB += state[cmd]

    hr = calc_headroom()

    if hr >= 0:

        match cmd:
            case 'level':        result = set_level(dB)
            case 'lu_offset':    result = set_lu_offset(dB)
            case 'bass':         result = set_bass(dB)
            case 'treble':       result = set_treble(dB)
            case 'tone_defeat':  result = set_tone_defeat(tone_defeat)
            case 'target':       result = set_target(tID)

    else:
        result = 'no headroom'

    if result == 'done':

        if cmd == 'target':
            state['target'] = tID
        elif cmd == 'tone_defeat':
            state["tone_defeat"] = tone_defeat
        else:
            state[cmd] = dB
        state["gain_headroom"] = hr

    # tones can be clamped when ordered out of range
    elif 'clamped' in result:

        state[cmd] = x2float(result.split()[-1])
        state["gain_headroom"] = hr

    return result


def normalize_cmd(cmd):
    """ Some alias are accepted for some commands """
    try:
        cmd = {
                'loudness':     'equal_loudness',
                'set_target':   'target',
                'drc':          'set_drc',
                'xo':           'set_xo',
                'input':        'set_input',
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
                result = set_loudness(mode=new_mode)
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

        case 'set_input':
            new = args
            if new in INPUTS:
                if state["input"] != new:
                    result = set_input(new)
                    if result == 'done':
                        state["input"] = new

        # Level related commands
        case 'level' | 'lu_offset' | 'bass' | 'treble':
            dB = x2float(args)
            result = do_levels(cmd, dB=dB, add=add)

        case 'target':
            newt = args
            if newt in TARGET_SETS + ['none']:
                if state["target"] != newt:
                    result = do_levels('target', tID=newt)

        case 'tone_defeat':
            curr =  state['tone_defeat']
            new = switch(args, curr)
            if type(new) == bool and new != curr:
                result = do_levels('tone_defeat', tone_defeat=new)

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
