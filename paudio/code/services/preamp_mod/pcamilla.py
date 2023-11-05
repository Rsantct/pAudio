#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  subprocess as sp
from    time import sleep
import  yaml
import  json
from    camilladsp import CamillaConnection
import  make_eq as mkeq

# This import works because the main program server.py
# is located under the code/share folder
from    common import *

#
# (i) use set_config_sync(some_config) to upload a new one
#

THIS_DIR = os.path.dirname(__file__)
CFG_PATH = f'{THIS_DIR}/camilladsp.yml'


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

def clear_pipeline_drc(cfg):
    for n in (1,2):
        names_old = cfg["pipeline"][n]['names']
        names_new = list_remove_by_pattern(names_old, 'drc.')
        cfg["pipeline"][n]['names'] = names_new
    return cfg


def make_pipeline_drc(cfg, drcID):
    for n in (1,2):
        names_old = cfg["pipeline"][n]['names']
        names_new = list_remove_by_pattern(names_old, 'drc.')
        names_new.insert(1, f'drc.L.{drcID}')
        cfg["pipeline"][n]['names'] = names_new
    return cfg


def init_camilladsp(user_config):
    """ Updates camilladsp.yml with user configs,
        includes auto making the DRC yaml stuff,
        then runs the CamillaDSP process.
    """

    def update_config_yml():
        """ Updates camilladsp.yml with user configs
        """

        def update_drc_stuff(cfg):

            def clear_drc_filters(cfg):
                keys = []
                for f in cfg["filters"]:
                    if f.startswith('drc.'):
                        keys.append(f)
                for k in keys:
                    del cfg["filters"][k]
                return cfg


            def make_drc_filters(cfg):
                lspk = user_config["loudspeaker"]
                for ID in user_config["drc_sets"]:
                    for Ch in 'L', 'R':
                        # We prefer relative paths from where the main program is launched,
                        # i.e. the ~/paudio folder, so that the yaml file does not have private paths.
                        fir_path = f'{LSPKSFOLDER}/{lspk}/drc.{Ch}.{ID}.pcm'
                        cfg["filters"][f'drc.{Ch}.{ID}'] = {}
                        f = cfg["filters"][f'drc.{Ch}.{ID}']
                        f["type"] = 'Conv'
                        f["parameters"] = {}
                        f["parameters"]["filename"] = fir_path
                        f["parameters"]["format"] = 'FLOAT32LE'
                        f["parameters"]["type"] = 'Raw'
                return cfg


            # drc filters
            clear_drc_filters(cfg)
            make_drc_filters(cfg)

            # The initial pipeline points to the FIRST drc_set
            clear_pipeline_drc(cfg)
            make_pipeline_drc(cfg, user_config["drc_sets"][0])

            return cfg


        def update_eq_filter(cfg):
            """ with proper path """
            cfg["filters"]["eq"]["parameters"]["filename"] = f'{EQFOLDER}/eq_flat.pcm'


        def update_dither(cfg):

            def check_bit_depth():
                if not( type(bits) == int and bits in range(2, 33)):
                    print(f'{Fmt.BOLD}BAD pbk_device_bit_depth: {bits}{Fmt.END}')
                    result = False
                elif bits not in (16, 24):
                    print(f'{Fmt.BOLD}Using rare dither bit depth: {bits}{Fmt.END}')
                    result = True
                else:
                    print(f'{Fmt.BOLD}{Fmt.BLUE}Using dither bit depth: {bits}{Fmt.END}')
                    result = True
                return result

            def make_dither_filter(d_type, bits):
                cfg["filters"]["dither"] = {
                    'type': 'Dither',
                    'parameters': {
                        'type': d_type, 'bits': bits
                    }
                }


            def add_dither_to_pipeline():
                cfg["pipeline"][1]["names"].append('dither')
                cfg["pipeline"][2]["names"].append('dither')


            bits = 0
            fs   = user_config["fs"]

            if "pbk_device_bit_depth" in user_config and user_config["pbk_device_bit_depth"]:
                bits = user_config["pbk_device_bit_depth"]

            if check_bit_depth():
                match fs:
                    case 44100:     d_type = 'Shibata441'
                    case 48000:     d_type = 'Shibata48'
                    case _:         d_type = 'Simple'
                make_dither_filter(d_type, bits)
                add_dither_to_pipeline()



        with open(CFG_PATH, 'r') as f:
            camilla_cfg = yaml.safe_load(f)

        # Audio Device
        camilla_cfg["devices"]["playback"]["device"] = user_config["device"]
        camilla_cfg["devices"]["samplerate"]         = user_config["fs"]

        # Dither
        update_dither(camilla_cfg)

        # The preamp_mixer
        camilla_cfg["mixers"]["preamp_mixer"] = make_mixer(midside_mode='normal')

        # eq filter
        update_eq_filter(camilla_cfg)

        # DRCs
        if user_config["drc_sets"]:
            camilla_cfg = update_drc_stuff(camilla_cfg)

        with open(CFG_PATH, 'w') as f:
            yaml.safe_dump(camilla_cfg, f)


    global PC

    # Updating user configs ---> camilladsp.yml
    update_config_yml()

    # Starting CamillaDSP with <camilladsp.yml> <muted>
    sp.call('pkill camilladsp'.split())
    cdsp_cmd = f'camilladsp -m -a 127.0.0.1 -p 1234'
    cdsp_cmd += f' "{CFG_PATH}"'
    sp.Popen( cdsp_cmd, shell=True )
    sleep(1)

    try:
        PC = CamillaConnection("127.0.0.1", 1234)
        PC.connect()
        return 'done'

    except Exception as e:
        return str(e)


def set_config_sync(cfg):
    """ (i) When ordering set_config some time is needed to be running
        This is a fake sync, but it works
    """
    PC.set_config(cfg)
    sleep(.1)


def get_state():
    """ This is the internal camillaDSP state """
    return PC.get_state()


def get_config():
    return PC.get_config()


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
        sp.call(f'rm {eq_link}'.split())
        sp.Popen(f'ln -s {eq_path} {eq_link}'.split())
    except Exception as e:
        print(f'Problems making the symlink eq/eq.pcm: {str(e)}')

    cfg = PC.get_config()
    cfg["filters"]["eq"]["parameters"]["filename"] = eq_path
    set_config_sync(cfg)

    toggle_last_eq()


def make_mixer(midside_mode='normal'):
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


def add_dither():
    pass

# Getting AUDIO

def get_drc_sets():
    """ Retrieves thr drc.X.XXX filters in camillaDSP configuration
    """
    filters = PC.get_config()["filters"]
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
    return json.dumps( PC.get_config()["filters"]["drc_gain"] )


# Setting AUDIO, allways **MUST** return some string, usually 'done'

def set_mute(mode):
    if type(mode) != bool:
        return 'must be True/False'
    res = str( PC.set_mute(mode) )
    if res == 'None':
        res = 'done'
    return res


def set_midside(mode):

    modes = ('off', 'mid', 'side', 'solo_L', 'solo_R')

    if mode in modes:
        c = PC.get_config()
        if mode == 'off':
            mode = 'normal'
        c["mixers"]["preamp_mixer"] = make_mixer(midside_mode = mode)
        set_config_sync(c)
        return 'done'

    else:
        return f'mode error must be in: {modes}'


def set_solo(mode):
    c = PC.get_config()
    match mode:
        case 'l':       m = make_mixer(midside_mode='solo_L')
        case 'r':       m = make_mixer(midside_mode='solo_R')
        case 'off':     m = make_mixer(midside_mode='normal')
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

    c = PC.get_config()

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
    res = str( PC.set_volume(dB) )
    if res == 'None':
        res = 'done'
    return res


def set_balance(dB):
    """ negative dBs means towards Left, positive to Right
    """
    c = PC.get_config()
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

    cfg = PC.get_config()

    if drcID == 'none':
        try:
            cfg = clear_pipeline_drc(cfg)
            set_config_sync(cfg)
            result = 'done'
        except Exception as e:
            result = str(e)

    else:
        try:
            cfg = make_pipeline_drc(cfg, drcID)
            set_config_sync(cfg)
            result = 'done'
        except Exception as e:
            result = str(e)

    return result


def set_drc_gain(dB):
    cfg = PC.get_config()
    cfg["filters"]["drc_gain"]["parameters"]["gain"] = dB
    set_config_sync(cfg)
    return 'done'


def set_lu_offset(dB):
    cfg = PC.get_config()
    cfg["filters"]["lu_offset"]["parameters"]["gain"] = dB
    set_config_sync(cfg)
    return 'done'

