#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  subprocess as sp
from    time import sleep
import  yaml
import  json
from    camilladsp import CamillaClient
import  make_eq as mkeq

# This import works because the main program server.py
# is located under the same folder then the commom module
from    common import *

#
# (i) use set_config_sync(some_config) to upload a new one
#

THIS_DIR = os.path.dirname(__file__)
CFG_PATH = f'{THIS_DIR}/camilladsp.yml'

# Can be disabled for terminal debug
LOG_TO_FILE = True
LOG_PATH    = f'{DSP_LOGFOLDER}/camilladsp.log'

# The CamillaDSP connection
PC = None

# CamillaDSP needs a new FIR filename in order to
# reload the convolver coeffs
last_eq = 'A'
eq_flat_path = f'{EQFOLDER}/eq_flat.pcm'
eq_A_path    = f'{EQFOLDER}/eq_A.pcm'
eq_B_path    = f'{EQFOLDER}/eq_B.pcm'
eq_link      = f'{EQFOLDER}/eq.pcm'
sp.Popen(f'cp {eq_flat_path} {eq_A_path}', shell=True)
sp.Popen(f'cp {eq_flat_path} {eq_B_path}', shell=True)



# INTERNAL

def init_camilladsp(pAudio_config):
    """ Updates camilladsp.yml with user configs,
        includes auto making the DRC yaml stuff,
        then runs the CamillaDSP process.
    """

    def update_config_yml():
        """ Updates camilladsp.yml with user configs
        """


        def update_xo_stuff(cfg):

            # xo filters
            clear_filters(cfg, pattern='xo.')
            for xoset in ('lo.mp', 'hi.mp'):
                cfg["filters"][f'xo.{xoset}'] = make_xo_filter(xoset)

            # pipeline PENDING


        def update_drc_stuff(cfg):

            # drc filters
            clear_filters(cfg, pattern='drc.')
            for drcset in pAudio_config["drc_sets"]:
                for ch in 'L', 'R':
                    cfg["filters"][f'drc.{ch}.{drcset}'] = make_drc_filter(ch, drcset)

            # The initial pipeline points to the FIRST drc_set
            clear_pipeline_input_filters(cfg, pattern='drc.')
            insert_drc_to_pipeline(cfg, drcID=pAudio_config["drc_sets"][0])


        def update_eq_filter(cfg):
            """ with proper path """
            cfg["filters"]["eq"]["parameters"]["filename"] = f'{EQFOLDER}/eq_flat.pcm'


        def update_dither(cfg):

            def check_bits():

                if not( type(bits) == int and bits in range(2, 33)):
                    print(f'{Fmt.BOLD}BAD dither_bits: {bits}{Fmt.END}')
                    result = False

                elif bits not in (16, 24):
                    print(f'{Fmt.BOLD}Using rare {bits} dither_bits' \
                          f' over the output {pbk_bit_depth} bits depth{Fmt.END}')
                    result = True

                else:
                    print(f'{Fmt.BOLD}{Fmt.BLUE}Using {bits} dither_bits' \
                          f' over the output {pbk_bit_depth} bits depth{Fmt.END}')
                    result = True

                return result


            fs              = cfg["devices"]["samplerate"]
            cap_fmt         = cfg["devices"]["capture"]["format"]
            pbk_fmt         = cfg["devices"]["playback"]["format"]
            cap_bit_depth   = get_bit_depth(cap_fmt)
            pbk_bit_depth   = get_bit_depth(pbk_fmt)
            bits            = 0


            # clearing
            clear_filters(cfg, pattern='dither')
            clear_pipeline_input_filters(cfg, pattern='dither')

            if "dither_bits" in pAudio_config["output"] and \
               pAudio_config["output"]["dither_bits"]:
                bits = pAudio_config["output"]["dither_bits"]

            if not bits:
                print(f'{Fmt.BLUE}- No dithering -{Fmt.END}')
                return

            if check_bits():

                # https://github.com/HEnquist/camilladsp#dither
                match fs:
                    case 44100:     d_type = 'Shibata441'
                    case 48000:     d_type = 'Shibata48'
                    case _:         d_type = 'Simple'

                cfg["filters"]["dither"] = make_dither_filter(d_type, bits)
                append_item_to_pipeline(cfg, item='dither')


        with open(CFG_PATH, 'r') as f:
            camilla_cfg = yaml.safe_load(f)

        # Audio Device
        # Updating with pAudio config

        camilla_cfg["devices"]["samplerate"] = pAudio_config["fs"]

        if camilla_cfg["devices"]["samplerate"] <= 48000:
            camilla_cfg["devices"]["chunksize"] = 1024
        else:
            camilla_cfg["devices"]["chunksize"] = 2048

        cap_dev = camilla_cfg["devices"]["capture"]
        pbk_dev = camilla_cfg["devices"]["playback"]

        if 'sound_server' in pAudio_config and pAudio_config["sound_server"]:
            cap_dev["type"] = pAudio_config["sound_server"]
            pbk_dev["type"] = pAudio_config["sound_server"]
            if cap_dev["type"].lower() == 'coreaudio':
                cap_dev["type"] = 'CoreAudio'
            if pbk_dev["type"].lower() == 'coreaudio':
                pbk_dev["type"] = 'CoreAudio'
        else:
            cap_dev["type"] = 'CoreAudio'
            pbk_dev["type"] = 'CoreAudio'

        cap_dev["device"] = pAudio_config["input"]["device"]
        cap_dev["format"] = pAudio_config["input"]["format"]
        pbk_dev["device"] = pAudio_config["output"]["device"]
        pbk_dev["format"] = pAudio_config["output"]["format"]

        # Number of channels to use
        N = get_number_of_ways()
        pbk_dev["channels"] = N * 2

        # MacOS Coreaudio exclusive mode
        if 'exclusive_mode' in pAudio_config["output"] and pAudio_config["output"]["exclusive_mode"] == True:
            pbk_dev["exclusive"] = True
        else:
            pbk_dev["exclusive"] = False

        # Dither
        update_dither(camilla_cfg)

        # The preamp_mixer
        camilla_cfg["mixers"]["preamp_mixer"] = make_preamp_mixer(midside_mode='normal')

        # The eq filter
        update_eq_filter(camilla_cfg)

        # The DRCs
        if pAudio_config["drc_sets"]:
            update_drc_stuff(camilla_cfg)
        else:
            clear_filters(camilla_cfg, pattern='drc.')
            clear_pipeline_input_filters(camilla_cfg, pattern='drc.')


        # The N ways expander Mixer
        make_N_way_mixer(camilla_cfg, N)
        tmp = {'type': 'Mixer', 'name': f'from2to{N*2}channels'}
        clear_pipeline_mixer(camilla_cfg, pattern='from2to')
        camilla_cfg["pipeline"].append(tmp)


        # The XO
        update_xo_stuff(camilla_cfg)


        # Saving to YAML file to run CamillaDSP
        with open(CFG_PATH, 'w') as f:
            yaml.safe_dump(camilla_cfg, f)


    global PC

    # Updating user configs ---> camilladsp.yml
    update_config_yml()

    # Starting CamillaDSP with <camilladsp.yml> and <muted>
    sp.call('pkill camilladsp'.split())
    cdsp_cmd = f'camilladsp -m -a 127.0.0.1 -p 1234'
    cdsp_cmd += f' "{CFG_PATH}"'
    if LOG_TO_FILE:
        cdsp_cmd += f' --logfile "{LOG_PATH}"'
    sp.Popen( cdsp_cmd, shell=True )
    sleep(1)

    try:
        PC = CamillaClient("127.0.0.1", 1234)
        PC.connect()
        return 'done'

    except Exception as e:
        return str(e)


def clear_filters(cfg, pattern=''):
    if pattern:
        keys = []
        for f in cfg["filters"]:
            if f.startswith(pattern):
                keys.append(f)
        for k in keys:
            del cfg["filters"][k]
    return cfg


def clear_pipeline_input_filters(cfg, pattern=''):
    """ Clears elements inside the 2 first filters of the pipeline.
        That is, the pipeline steps 1 and 2
    """
    if pattern:
        for n in (1, 2):
            names_old = cfg["pipeline"][n]['names']
            names_new = list_remove_by_pattern(names_old, pattern)
            cfg["pipeline"][n]['names'] = names_new


def clear_pipeline_mixer(cfg, pattern=''):
    """ Clears mixer steps from the pipeline
    """
    def remove_mixer(l, p):
        l = [ x for x in l
                if (x["type"]=='Mixer' and p not in x["name"])
                   or
                   x["type"]!='Mixer'
            ]
        return l

    if pattern:
        steps_old = cfg["pipeline"]
        steps_new = remove_mixer(steps_old, pattern)
        cfg["pipeline"] = steps_new


def insert_drc_to_pipeline(cfg, drcID = ''):
    for n in (1,2):
        names_old = cfg["pipeline"][n]['names']
        names_new = list_remove_by_pattern(names_old, 'drc.')
        names_new.insert(1, f'drc.L.{drcID}')
        cfg["pipeline"][n]['names'] = names_new
    return cfg


def append_item_to_pipeline(cfg, item = ''):
    for n in (1,2):
        names_old = cfg["pipeline"][n]['names']
        names_new = list_remove_by_pattern(names_old, item)
        names_new.append(item)
        cfg["pipeline"][n]['names'] = names_new
    return cfg


def set_config_sync(cfg):
    """ (i) When ordering set config some time is needed to be running
        This is a fake sync, but it works
    """
    PC.config.set_active(cfg)
    sleep(.1)


def get_state():
    """ This is the internal camillaDSP state """
    return PC.general.state()


def get_config():
    return PC.config.active()


def reload_eq():

    def toggle_last_eq():
        global last_eq
        last_eq = {'A':'B', 'B':'A'}[last_eq]


    mkeq.make_eq()
    eq_path  = f'{EQFOLDER}/eq_{last_eq}.pcm'
    mkeq.save_eq_IR(eq_path)

    # For convenience, it will be copied to eq.pcm,
    # so that a viewer could display the current curve
    try:
        with open('/dev/null', 'r') as fnull:
            sp.call(f'rm {eq_link}'.split(), stdout=fnull, stderr=fnull)
            sp.call(f'ln -s {eq_path} {eq_link}'.split(), stdout=fnull, stderr=fnull)
    except Exception as e:
        print(f'Problems making the symlink eq/eq.pcm: {str(e)}')

    cfg = PC.config.active()
    cfg["filters"]["eq"]["parameters"]["filename"] = eq_path
    set_config_sync(cfg)

    toggle_last_eq()


def make_dither_filter(d_type, bits):
    f= {
        'type': 'Dither',
        'parameters': {
            'type': d_type,
            'bits': bits
        }
    }
    return f


def make_drc_filter(channel, drc_set):
    fir_path = f'{LSPKFOLDER}/drc.{channel}.{drc_set}.pcm'
    f = {
            "type": 'Conv',
            "parameters": {
                "filename": fir_path,
                "format":   'FLOAT32LE',
                "type":     'Raw'
            }
        }
    return f


def make_xo_filter(xo_set):
    fir_path = f'{LSPKFOLDER}/xo.{xo_set}.pcm'
    f = {
            "type": 'Conv',
            "parameters": {
                "filename": fir_path,
                "format":   'FLOAT32LE',
                "type":     'Raw'
            }
        }
    return f


def make_preamp_mixer(midside_mode='normal'):
    """
        modes:

            normal
            mid     (mono)
            side    (L-R)
            solo_L
            solo_R

        A mixer layout:

                        dest 0
            in 0  --------  00
                   \  ____  10
                    \/
                    /\____
                   /        01      "01" means source 0  dest 1
            in 1  --------  11
                        dest 1

        Gain, Inverted and Mute settings in 'normal' mode

        in 0            in 1
           |               |
           |               |

        G inv mut       G inv mut

        0   F   F       0   F   T   --> dest 0

        0   F   T       0   F   F   --> dest 1
    """

    match midside_mode:

        case 'normal':
            g00 =  0.0; i00 = False; m00 = False;    g10 =  0.0; i10 = False; m10 = True
            g01 =  0.0; i01 = False; m01 = True;     g11 =  0.0; i11 = False; m11 = False

        case 'mid':
            g00 = -6.0; i00 = False; m00 = False;    g10 = -6.0; i10 = False; m10 = False
            g01 = -6.0; i01 = False; m01 = False;    g11 = -6.0; i11 = False; m11 = False

        case 'side':
            g00 =  0.0; i00 = False; m00 = False;    g10 =  0.0; i10 = False; m10 = True
            g01 =  0.0; i01 = False; m01 = True;     g11 =  0.0; i11 = True; m11 = False

        case 'solo_L':
            g00 =  0.0; i00 = False; m00 = False;    g10 =  0.0; i10 = False; m10 = True
            g01 =  0.0; i01 = False; m01 = True;     g11 =  0.0; i11 = False; m11 = True

        case 'solo_R':
            g00 =  0.0; i00 = False; m00 = True;     g10 =  0.0; i10 = False; m10 = True
            g01 =  0.0; i01 = False; m01 = True;     g11 =  0.0; i11 = False; m11 = False


    m = {
        'channels': { 'in': 2, 'out': 2 },
        'mapping': [
            {   'dest': 0,
                'sources': [
                    {'channel': 0, 'gain': g00, 'inverted': i00, 'mute': m00},
                    {'channel': 1, 'gain': g10, 'inverted': i10, 'mute': m10},
                ]
            },
            {   'dest': 1,
                'sources': [
                    {'channel': 0, 'gain': g01, 'inverted': i01, 'mute': m01},
                    {'channel': 1, 'gain': g11, 'inverted': i11, 'mute': m11},
                ]
            }
        ]
    }

    return m


def make_N_way_mixer(cfg, N):
    """
    Example:

      from2to4channels:
        channels:
          in: 2
          out: 4
        mapping:
        - dest: 0
          sources:
          - channel: 0
        - dest: 1
          sources:
          - channel: 1
        - dest: 2
          sources:
          - channel: 0
        - dest: 3
          sources:
          - channel: 1
    """

    mixer_name = f'from2to{N * 2}channels'
    cfg["mixers"][mixer_name] = {'channels': {'in': 2, 'out': N * 2},
                                 'mapping': []}

    for d in range(N):
        for s in (0,1):
            tmp = {'dest': d, 'sources': [{'channel': s}]}
            cfg["mixers"][mixer_name]["mapping"].append(tmp)


def get_number_of_ways():

    outputs = CONFIG["outputs"]

    L_outs  = [ o for o, ps in outputs.items() if ps["name"][-1]=='L' ]
    R_outs  = [ o for o, ps in outputs.items() if ps["name"][-1]=='R' ]
    SW_outs = [ o for o, ps in outputs.items() if 'sw' in ps["name"]  ]

    if len(L_outs) != len(R_outs):
        raise Exception('Number of outputs for L and R does not match')

    return len(L_outs)


# Getting AUDIO

def get_drc_sets():
    """ Retrieves thr drc.X.XXX filters in camillaDSP configuration
    """
    filters = PC.config.active()["filters"]
    drc_sets = []
    for f in filters:
        if f.startswith('drc.'):
            drc_set = f.split('.')[-1]
            if not drc_set in drc_sets:
                drc_sets.append(drc_set)
    return drc_sets


def get_xo_sets():
    return []


def get_drc_gain():
    return json.dumps( PC.config.active()["filters"]["drc_gain"] )


# Setting AUDIO, allways **MUST** return some string, usually 'done'

def set_mute(mode):
    if type(mode) != bool:
        return 'must be True/False'
    res = str( PC.mute.set_main(mode) )
    if res == 'None':
        res = 'done'
    return res


def set_midside(mode):

    modes = ('off', 'mid', 'side', 'solo_L', 'solo_R')

    if mode in modes:
        c = PC.config.active()
        if mode == 'off':
            mode = 'normal'
        c["mixers"]["preamp_mixer"] = make_mixer(midside_mode = mode)
        set_config_sync(c)
        return 'done'

    else:
        return f'mode error must be in: {modes}'


def set_solo(mode):
    c = PC.config.active()
    match mode:
        case 'l':       m = make_preamp_mixer(midside_mode='solo_L')
        case 'r':       m = make_preamp_mixer(midside_mode='solo_R')
        case 'off':     m = make_preamp_mixer(midside_mode='normal')
        case _:         return 'solo mode must be L|R|off'
    c["mixers"]["preamp_mixer"] = m
    set_config_sync(c)
    return "done"


def set_polarity(mode):
    """ Polarity applied to channels
    """
    if mode in ('normal','off'):    mode = '++'

    modes = ('++', '--', '+-', '-+')

    result = f'Polarity must be in: {modes}'

    c = PC.config.active()

    match mode:

        case '++':      inv_L = False;   inv_R = False
        case '--':      inv_L = True;    inv_R = True
        case '+-':      inv_L = False;   inv_R = True
        case '-+':      inv_L = True;    inv_R = False

    c["filters"]["bal_pol_L"]["parameters"]["inverted"] = inv_L
    c["filters"]["bal_pol_R"]["parameters"]["inverted"] = inv_R

    set_config_sync(c)

    return "done"


def set_volume(dB):
    res = str( PC.volume.set_main(dB) )
    if res == 'None':
        res = 'done'
    return res


def set_balance(dB):
    """ negative dBs means towards Left, positive to Right
    """
    c = PC.config.active()
    c["filters"]["bal_pol_L"]["parameters"]["gain"] = -dB / 2.0
    c["filters"]["bal_pol_R"]["parameters"]["gain"] = +dB / 2.0
    set_config_sync(c)
    return "done"


def set_treble(dB):
    result = 'done'
    # curves are from -12...+12 in 1 dB step
    if abs(dB) > 12:
        dB = max(-12, min(+12, dB))
        result = f'treble clamped to {dB}'
    if int(dB) != float(dB):
        dB = int(round(float(dB)))
        result = f'treble rounded to {dB}'
    mkeq.treble = float(dB)
    reload_eq()
    return result


def set_bass(dB):
    result = 'done'
    # curves are from -12...+12 in 1 dB step
    if abs(dB) > 12:
        dB = max(-12, min(+12, dB))
        result = f'bass clamped to {dB}'
    if int(dB) != float(dB):
        dB = int(round(float(dB)))
        result = f'bass rounded to {dB}'
    mkeq.bass = float(dB)
    reload_eq()
    return result


def set_target(tID):
    try:
        if tID == 'none':
            tID = '+0.0-0.0'
        mkeq.target = tID
        reload_eq()
        return 'done'
    except Exception as e:
        return f'target error: {str(e)}'


def set_loudness(mode, level):
    if type(mode) != bool:
        return 'must be True/False'
    spl = level + mkeq.LOUDNESS_REF_LEVEL
    mkeq.spl            = spl
    mkeq.equal_loudness = mode
    reload_eq()
    return 'done'


def set_xo(xoID):
    """ PENDING
        xoID cannot be 'none'
    """
    result = 'XO pending'
    return result


def set_drc(drcID):

    result = ''

    cfg = PC.config.active()

    if drcID == 'none':
        try:
            cfg = clear_pipeline_input_filters(cfg, pattern='drc.')
            set_config_sync(cfg)
            result = 'done'
        except Exception as e:
            result = str(e)

    else:
        try:
            insert_drc_to_pipeline(cfg, drcID)
            set_config_sync(cfg)
            result = 'done'
        except Exception as e:
            result = str(e)

    return result


def set_drc_gain(dB):
    cfg = PC.config.active()
    cfg["filters"]["drc_gain"]["parameters"]["gain"] = dB
    set_config_sync(cfg)
    return 'done'


def set_lu_offset(dB):
    cfg = PC.config.active()
    cfg["filters"]["lu_offset"]["parameters"]["gain"] = dB
    set_config_sync(cfg)
    return 'done'

