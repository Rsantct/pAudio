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

# This import works because the main program server.py
# is located under the code/share folder
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

# INIT
def init():

    global state, CONFIG, INPUTS, TARGET_SETS, DRC_SETS, XO_SETS

    INPUTS      = CONFIG["inputs"]
    TARGET_SETS = get_target_sets(fs=CONFIG["fs"])
    DRC_SETS    = get_drc_sets_from_loudspeaker(CONFIG["loudspeaker"])
    XO_SETS     # PENDING


    # Default CONFIG values
    if not "tones_span_dB" in CONFIG:
        CONFIG["tones_span_dB"] = 6.0


    # Optional user configs having precedence over the saved state:
    for prop in 'level', 'balance', 'bass', 'treble', 'lu_offset', \
                'equal_loudness', 'target', 'drc_set':

        if prop in CONFIG:

            # Some validation
            match prop:

                case 'target':
                    if CONFIG["target"] in TARGET_SETS + ['none']:
                        state["target"] = CONFIG["target"]
                    else:
                        print(f'{Fmt.BOLD}ERROR in config target{Fmt.END}')

                case 'drc_set':
                    if CONFIG["drc_set"] in DRC_SETS + ['none']:
                        state["drc_set"] = CONFIG["drc_set"]
                    else:
                        print(f'{Fmt.BOLD}ERROR in config drc_set{Fmt.END}')

                case _:
                    state[prop] = CONFIG[prop]


    # state FS is just informative
    state["fs"] = CONFIG["fs"]


    # Preparing and running camillaDSP

    DSP.init_camilladsp(user_config=CONFIG, drc_sets=DRC_SETS)


    # Resuming audio settings

    do_levels( 'level', dB=state["level"] )

    do_levels( 'balance', dB=state["balance"] )

    set_mute( state["muted"] )

    set_solo( state["solo"] )

    # tones can be clamped when ordered out of range
    res = do_levels( 'bass', dB=state["bass"] )
    if res != 'done':
        print(f'{Fmt.BOLD}{res}{Fmt.END}')
        state["bass"] = x2int(res.split()[-1])

    res = do_levels( 'treble', dB=state["treble"] )
    if res != 'done':
        print(f'{Fmt.BOLD}{res}{Fmt.END}')
        state["treble"] = x2int(res.split()[-1])

    do_levels( 'lu_offset', dB=state["lu_offset"] )

    do_levels( 'target', tID=state["target"] )

    set_loudness( mode=state["equal_loudness"] )

    set_drc( state["drc_set"] )

    # XO is pending
    #set_xo( state["xo_set"] )

    # Saving state with user settings
    save_json_file(state, STATE_PATH)

    return


# Interface functions with the underlying modules

def set_mute(mode):
    return DSP.set_mute(mode)


def set_midside(mode):
    return DSP.set_midside(mode)


def set_solo(mode):
    result = 'needs L|R|off'
    match mode:
        case 'L'|'R'|'off':     result = DSP.set_solo(mode)
    return result


def set_loudness(mode, level=state["level"]):
    spl = level + 83.0
    result = DSP.set_loudness(mode, spl)
    return result


def set_drc(drcID):

    if not DRC_SETS:
        res = 'not available'

    elif not drcID in DRC_SETS + ['none']:
        res = f'must be in: {DRC_SETS}'

    else:
        # camillaDSP has not gain setting for a FIR filter,
        # so it must be done outside

        # Because DRCs are assumed to have negative gain, we first
        # put down volume when drc='none'
        if drcID == 'none':
            DSP.set_drc_gain(DRCS_GAIN)

        res = DSP.set_drc(drcID)

        if res == 'done' and drcID != 'none':
            DSP.set_drc_gain(0.0)

    return res


def set_xo(xoID):

    if not XO_SETS:
        res = 'not available'

    elif not xoID in XO_SETS:
        res = f'must be in: {XO_SETS}'

    else:
        res = DSP.set_xo(xoID)

    return res


def set_input(inputID):
    """ fake selector """
    if inputID in INPUTS:
        res = 'done'
    else:
        res = f'must be in: {INPUTS}'
    return res


def do_levels(cmd, dB=0.0, tID='+0.0-0.0', tone_defeat='False', add=False):
    """ Level related commands
    """

    def set_level(dB):
        DSP.set_volume(dB)
        return set_loudness(mode=state["equal_loudness"], level=dB)


    def set_balance(dB):
        return DSP.set_balance(dB)


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

        hr = - candidate["level"] + candidate["lu_offset"] \
             - abs(candidate["balance"])/2.0 \
             - DRCS_GAIN

        if not candidate["tone_defeat"]:

            if candidate["bass"] > 0:
                hr -= candidate["bass"]

            if candidate["treble"] > 0:
                hr -= candidate["treble"]

        if candidate["target"] != 'none':
            tgain = x2float( candidate["target"][:4] )
            if tgain > 0:
                hr -= tgain

        return round(hr, 1)


    # getting absolute values from relative command
    if add:
        dB += state[cmd]

    clamped = ''
    tmax = CONFIG["tones_span_dB"]
    if cmd in ('bass', 'treble'):
        if abs(dB) > tmax:
            dB = max(-tmax, min(+tmax, dB))
            clamped = str(dB)

    hr = calc_headroom()

    if hr >= 0:

        match cmd:

            case 'level':
                result = set_level(dB)

            case 'balance':
                result = set_balance(dB)

            case 'lu_offset':
                result = set_lu_offset(dB)

            case 'bass':
                result = set_bass(dB)
                if result != 'done':
                    dB = x2int( result.split()[-1])
                    clamped = str(dB)
                    result = 'done'

            case 'treble':
                result = set_treble(dB)
                if result != 'done':
                    dB = x2int( result.split()[-1])
                    clamped = str(dB)
                    result = 'done'

            case 'tone_defeat':
                result = set_tone_defeat(tone_defeat)

            case 'target':
                result = set_target(tID)

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

    if clamped:
        result =  f'clamped to {dB}'

    return result


# Entry function
def do(cmd, args, add):

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

        case 'set_input':
            new = args
            if state["input"] != new:
                result = set_input(new)
                if result == 'done':
                    state["input"] = new

        case 'mono':
            result = 'needs: on|off|toggle'
            match args:
                case 'on':
                    new = 'mid'
                    result = set_midside(new)
                case 'off':
                    new = 'off'
                    result = set_midside(new)
                case 'toggle':
                    curr = state["midside"]
                    new = {'off':'mid', 'mid':'off', 'side':'off'}[curr]
                    result = set_midside(new)
            if result == 'done':
                state["midside"] = new

        case 'midside':
            new = args
            if state["midside"] != new:
                result = set_midside(new)
                if result == 'done':
                    state["midside"] = new

        case 'solo':
            new = args
            if state["solo"] != new:
                result = set_solo(new)
                if result == 'done':
                    state["solo"] = new

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
            new = args
            if state["drc_set"] != new:
                result = set_drc(new)
                if result == 'done':
                    state["drc_set"] = new

        case 'set_xo':
            new = args
            if state["xo_set"] != new:
                result = set_xo(new)
                if result == 'done':
                    state["xo_set"] = new

        # Level related commands
        case 'level' | 'lu_offset' | 'bass' | 'treble' | 'balance':
            try:
                dB = x2float(args)
                result = do_levels(cmd, dB=dB, add=add)
            except:
                result = 'needs a float value'

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
        case 'get_cdsp_config':
            result = DSP.get_config()

        case 'get_cdsp_preamp_mixer':
            result = DSP.get_config()["mixers"]["preamp_mixer"]

        case 'get_cdsp_pipeline':
            result = DSP.get_config()["pipeline"]

        case 'get_cdsp_drc_gain':
            result = DSP.get_drc_gain()

        case _:
            result = 'unknown command'

    if dosave:
        save_json_file(state, STATE_PATH)

    if type(result) != str:
        try:
            result = json.dumps(result)
        except Exception as e:
            result = f'Internal error: {e}'

    return result


init()
