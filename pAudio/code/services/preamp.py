#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Preamp subsystem.

    Version with CamillaDSP processor (https://github.com/HEnquist/camilladsp)

"""

import  sys
import  os
import  subprocess as sp
import  json

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')
sys.path.append(f'{MAINFOLDER}/code/services/preamp_mod')

from    common      import *
from    eqfir2png   import fir2png

# import Jack stuff ONLY with LINUX
if sys.platform == 'linux' and CONFIG.get('jack'):
    import  jack
    import  sources

import  pcamilla as DSP


STATE_PATH  = f'{MAINFOLDER}/.preamp_state'

#
# Main variable (preamplifier state)
#
state = read_json_file(STATE_PATH)


# INIT
def init():

    def resume_audio():

        do_levels( 'level', dB=state["level"] )

        set_polarity( state["polarity"] )

        set_solo( state["solo"] )

        do_levels( 'balance', dB=state["balance"] )

        set_mute( state["muted"] )

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

        if not state["drc_set"] in DRC_SETS:
            state["drc_set"] = 'none'
        set_drc( state["drc_set"] )

        if not state["xo_set"] in XO_SETS:
            state["xo_set"] = ''
        else:
            set_xo( state["xo_set"] )

        set_source(state["source"])


    global state, CONFIG, SOURCES, TARGET_SETS, DRC_SETS, XO_SETS

    # (i) SOURCES can be internally added for well known plugins,
    #     so the YAML configured has only the user defined ones.
    if 'sources' in sys.modules:
        SOURCES         = sources.SOURCES
    else:
        SOURCES         = {}

    TARGET_SETS         = get_target_sets(fs=CONFIG["samplerate"])

    DRC_SETS            = get_drc_sets_from_loudspeaker_folder()
    CONFIG["drc_sets"]  = DRC_SETS

    XO_SETS             = get_xo_sets_from_loudspeaker_folder()
    CONFIG["xo_sets"]   = XO_SETS


    # Optional user config settings having precedence over the saved state:
    for prop in 'level', 'balance', 'bass', 'treble', 'tone_defeat',  \
                'lu_offset', 'equal_loudness', 'target', 'drc_set':

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


    # Forced init settings
    state["loudspeaker"]    = CONFIG["loudspeaker"]
    state["fs"]             = CONFIG["samplerate"]
    state["polarity"]       = '++'


    if CONFIG.get('jack'):

        # open a temporary jack.Client
        jcli = jack.Client(name='tmp', no_start_server=True)

        if jcli.get_ports('system', is_physical=True, is_output=True):
            state["input_dev"]  = CONFIG["jack"]["device"]
        else:
            state["input_dev"]  = ''

        if jcli.get_ports('system', is_physical=True, is_input=True):
            state["output_dev"]  = CONFIG["jack"]["device"]
        else:
            state["output_dev"]  = ''

        # close the temporary jack.Client
        del jcli


        state["jack_buffer_size"] = CONFIG["jack"]["period"] * CONFIG["jack"]["nperiods"]
        state["jack_buffer_ms"]   = int(round(state["jack_buffer_size"] / state["fs"] * 1000))


    elif CONFIG.get('coreaudio'):
        state["input_dev"]  = CONFIG["coreaudio"]["devices"]["capture"] ["device"]
        state["output_dev"] = CONFIG["coreaudio"]["devices"]["playback"]["device"]

    else:
        state["input_dev"]  = 'unknown'
        state["output_dev"] = 'unknown'


    if not CONFIG.get('jack'):
        try:
            del state["jack_buffer_size"]
            del state["jack_buffer_ms"]
        except:
            pass


    state["dsp_buffer_size"]    = 0


    # Preparing and running camillaDSP
    run_cdsp = DSP.init_camilladsp( pAudio_config=CONFIG )

    if run_cdsp == 'done':

        state["dsp_buffer_size"] = DSP.CC.config.active()["devices"]["chunksize"]
        state["dsp_buffer_ms"]   = int(round(state["dsp_buffer_size"] / state["fs"] * 1000))

        # Changing MacOS default playback device
        # (It will be restored when ordering `paudio.sh stop`)
        if CONFIG.get('coreaudio'):
            save_default_sound_device()
            change_default_sound_device( CONFIG["coreaudio"]["devices"]["capture"]["device"] )

        # Resuming audio settings on the DSP
        resume_audio()

        # Saving state with user settings mods
        save_json_file(state, STATE_PATH)

    else:
        print(f'{Fmt.BOLD}ERROR RUNNING CamillaDSP, check:')
        print(f'    - The sound card is attached')
        print(f'    - The `config.yml` file')
        print(f'    - Logs under ~/pAudio/log/{Fmt.END}\n')
        sys.exit()


# Dumping EQ to .png file and alerting clients to let them know
def eq2png():

    def alert_new_eq_graph(timeout=1):
        """ This sets the 'new_eq_graph' field to True for a while
            so that the web page can realize when the graph is dumped.
            This helps on slow machines because the PNG graph takes a while
            after the 'done' is received when issuing some audio command.
        """

        def new_eq_graph(mode):
            aux_info = read_json_file(AUXINFO_PATH)
            aux_info['new_eq_graph'] = mode
            save_json_file(aux_info, AUXINFO_PATH)

        def mytimer(timeout):
            sleep(timeout)
            new_eq_graph(False)

        new_eq_graph(True)

        job = threading.Thread(target=mytimer, args=(timeout,))
        job.start()


    def do_graph(e):
        fir2png()
        e.set()


    def flag_to_aux_info(e):
        e.wait()    # waits until set flag is true
        alert_new_eq_graph()


    # Threading because saving the PNG file can take too long
    e  = threading.Event()
    j1 = threading.Thread(target=do_graph,         args=(e,))
    j2 = threading.Thread(target=flag_to_aux_info, args=(e,))
    j1.start()
    j2.start()


# Interface functions with the underlying modules

def set_mute(mode):
    return DSP.set_mute(mode)


def set_solo(mode):
    return DSP.set_solo(mode)


def set_polarity(mode):
    return DSP.set_polarity(mode)


def set_loudness(mode, level=state["level"]):
    result = DSP.set_loudness(mode, level)
    return result


def set_drc(drcID):

    if not DRC_SETS:
        res = 'not available'

    elif not drcID in DRC_SETS + ['none']:
        res = f'must be in: {DRC_SETS}'

    else:
        # camillaDSP has not gain setting for a FIR filter,
        # so it must be done outside

        # Because DRCs are supposed to have a non positive unity gain offset,
        # we first put down volume when drc='none'
        if drcID == 'none':
            tmp = DSP.set_drc_gain(CONFIG["drcs_offset"])

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


def set_source(sname):
    """ This works only with JACK
    """

    if not CONFIG.get('jack'):
        return 'source change only available with Jack backend.'

    if sname in SOURCES:
        res = sources.select( sname )

        if 'remote' in sname:

            # Example:
            # 'remoteSalon': {  'remote_delay': 0,
            #                   'remote_track_level': True,
            #                   'ip': '192.168.1.57',
            #                   'port': 9990,
            #                   'jport': 'zita_n2j_57'  }

            if SOURCES[sname].get('remote_track_level'):

                remote_ip               = SOURCES[sname].get('ip')
                remote_vol_daemon_port  = SOURCES[sname].get('port') + 5

                send_cmd('hello', host=remote_ip, port=remote_vol_daemon_port)

    else:
        res = f'must be in: {SOURCES.keys()}'

    return res


def do_levels(cmd, dB=0.0, tID='+0.0-0.0', tone_defeat='False', add=False):
    """ Level related commands
    """

    def set_level(dB):
        DSP.set_volume(dB + CONFIG["ref_level_gain_offset"] )
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

        hr = - candidate["level"]                           \
             + candidate["lu_offset"]                       \
             - CONFIG["ref_level_gain_offset"]              \
             - abs(candidate["balance"]) / 2.0              \
             - CONFIG["drcs_offset"]

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

        # dumps eq to png
        eq2png()

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
                    'input':        'set_source',
                    'source':       'set_source',
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

        case 'get_sources':
            result = json.dumps( list(SOURCES.keys()) )

        case 'get_target_sets':
            result = json.dumps(TARGET_SETS)

        case 'get_drc_sets':
            result = json.dumps(DRC_SETS)

        case 'get_xo_sets':
            result = json.dumps(XO_SETS)

        case 'set_source':
            new = args
            if state["source"] != new:
                result = set_source(new)
                if result in ('done', 'ordered'):
                    state["source"] = new

        case 'mono':

            # here we need to transate to internal `midside`

            result = 'needs: on | off | toggle'

            match args:

                case 'on':
                    new = 'mid'
                    result = DSP.set_midside(new)

                case 'off':
                    new = 'off'
                    result = DSP.set_midside(new)

                case 'toggle':
                    curr = state["midside"]
                    new = {'off': 'mid', 'mid': 'off', 'side': 'off'}[curr]
                    result = DSP.set_midside(new)

            if result == 'done':
                state["midside"] = new

        case 'midside':

            new = args

            if state["midside"] != new:
                result = set_midside(new)

                if result == 'done':
                    state["midside"] = new

        case 'solo':

            new = args.lower()

            if not new in state["solo"]:
                result = set_solo(new)

                if result == 'done':
                    state["solo"] = new

            return result

        case 'polarity':

            new = args

            if state["polarity"] != new:
                result = set_polarity(new)

                if result == 'done':
                    state["polarity"] = new

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
                # dumps eq to png
                eq2png()

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

        # Level related commands (state updated by do_levels)
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
