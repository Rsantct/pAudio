#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  sys
import  os
import  yaml
from    fmt                     import Fmt
from    pcamilla_mod.do_makes   import *

UHOME = os.path.expanduser('~')
MAINFOLDER          = f'{UHOME}/pAudio'

LSPKSFOLDER         = f'{MAINFOLDER}/loudspeakers'
LSPKFOLDER          = f''
LOUDSPEAKER         = f''   # to be found later
LSPK_YML_PATH       = f''   #

EQFOLDER            = f'{MAINFOLDER}/eq'
CODEFOLDER          = f'{MAINFOLDER}/code'
CONFIG_PATH         = f'{MAINFOLDER}/config.yml'
LOGFOLDER           = f'{MAINFOLDER}/log'
PLUGINSFOLDER       = f'{MAINFOLDER}/code/share/plugins'

LDCTRL_PATH         = f'{MAINFOLDER}/.loudness_control'
LDMON_PATH          = f'{MAINFOLDER}/.loudness_monitor'
AUXINFO_PATH        = f'{MAINFOLDER}/.aux_info'
PLAYER_META_PATH    = f'{MAINFOLDER}/.player_metadata'


try:
    os.mkdir(LOGFOLDER)
except:
    pass


def _init():

    def get_lspk_config():
        """
            - Read the loudspeaker's YAML file

            - Some sections can have simplified filter definitions,
              here will populate a complete CamillaDSP filter syntax

            - If outputs: section is NOT defined, defaults to an stereo ones

        """

        def load_lspk_config():

            res = {}

            if os.path.isfile(LSPK_YML_PATH):

                try:
                    with open(LSPK_YML_PATH, 'r') as f:
                        res = yaml.safe_load( f.read() )
                        print(f'{Fmt.BLUE}Loudspeaker {CONFIG["loudspeaker"]}/lspk.yml was found{Fmt.END}')

                except Exception as e:
                    print(f'{Fmt.RED}Cannot load {CONFIG["loudspeaker"]}/lspk.yml {str(e)}{Fmt.END}')

            return res


        def populate_lspk_eq_filters():
            """ currently lspk_eq filters are assumed to be in CamillaDSP format
            """
            pass


        def populate_drc_filters():
            """ - FIR have only the drc-set-name as values, so we need
                  to REPLACE it with the whole parameters for both channels.

                - IIR is assumed to have a regular complete filter syntax,
                  so nothing is done
            """

            for set_name, values in LSPK_CONFIG.get('drc', {}).items():

                if values.get('type', '') == 'fir':

                    fs = CONFIG["samplerate"]

                    # Keep gain_offset and prepare channels syntax
                    values = {'L': {}, 'R': {}, 'gain_offset': values.get('gain_offset', 0.0)}

                    for ch in 'L', 'R':

                        fir_path = f'{LSPKFOLDER}/{fs}/drc.{ch}.{set_name}.pcm'

                        values[ch]["1"] = make_fir_filter(fir_path)

                    LSPK_CONFIG["drc"][set_name] = values


        def populate_xo_filters():
            """ XO items in lspk.yml comes in a human readable format,
                here we complete a CamillaDSP syntax for them.

                Also will prepare an auxiliary CamillaDSP filter definition
                for gain on each xo-set-name-way
            """

            if not 'xo' in LSPK_CONFIG or not LSPK_CONFIG.get('xo'):
                return

            LSPK_CONFIG["xo_gains"] = {}

            for set_name, ways in LSPK_CONFIG["xo"].items():

                for way, params in ways.items():

                    # FIR
                    if params.get('type') == 'fir':
                        fir_path = f'{LSPKFOLDER}/{CONFIG["samplerate"]}/xo.{way}.{set_name}.pcm'
                        LSPK_CONFIG["xo"][set_name][way] = make_fir_filter(fir_path)

                    # IIR
                    else:
                        ftype, order, freq = params["type"], params["order"], params["freq"]
                        LSPK_CONFIG["xo"][set_name][way] = make_xo_iir_filter(way, ftype, order, freq)

                    gain = params.get('gain', 0.0)
                    LSPK_CONFIG["xo_gains"][f'{way}.{set_name}'] = gain


        def reformat_outputs():
            """
                Outputs are given in NON standard YML, having 4 fields.

                An output can be void, or at least must have a valid <Name>.

                Out# starts from 1 until the max number of available channels
                of the used sound card.

                Valid names are '[lo|mi|hi].[L|R]' or 'sw', e.g.: 'lo.L', 'hi.L'

                Example:

                    # Out       Name         Gain    Polarity  Delay (ms)
                    1:          lo.L          0.0       +       0.0
                    2:          lo.R          0.0       +       0.0
                    3:          hi.L          0.0       -       0.15
                    4:          hi.R          0.0       -       0.15
                    5:
                    6:          sw            0.0       +       0.0


                Here will convert the Human Readable fields into a dictionary.
            """

            def make_paudio_output(o_name, gain=0.0, polarity='+', delay=0.0):

                res = {
                    'name':         o_name,
                    'gain':         gain,
                    'polarity':     polarity,
                    'delay':        delay
                }

                return res


            def check_output_params(out, params):

                out_name, gain, pol, delay = params

                if not out_name or not out_name.replace('.', '').replace('_', '').isalpha():
                    raise Exception( f'Output {out} bad name: {out_name}' )

                if not out_name[:2] == 'sw' and not out_name[-2:] in ('.L', '.R'):
                    raise Exception( f'Output {out} bad name: {out_name}' )

                if gain:
                    gain = round(float(gain), 1)
                else:
                    gain = 0.0

                if pol:
                    valid_pol = ('+', '-', '1', '-1', 1, -1)
                    if not pol in valid_pol:
                        raise Exception( f'Polarity must be in {valid_pol}' )
                else:
                    pol = 1

                if delay:
                    delay = round(float(delay), 3)
                else:
                    delay = 0.0

                return out, (out_name, gain, pol, delay)


            def check_output_names():
                """ Check L/R pairs
                """
                outputs = LSPK_CONFIG["outputs"]

                L_outs  = [ pms["name"] for o, pms in outputs.items()
                            if pms["name"] and pms["name"][-1]=='L' ]
                R_outs  = [ pms["name"] for o, pms in outputs.items()
                            if pms["name"] and pms["name"][-1]=='R' ]

                if len(L_outs) != len(R_outs):
                    raise Exception('Number of outputs for L and R does not match')


            if not LSPK_CONFIG.get("outputs"):
                # Default to full range
                LSPK_CONFIG["outputs"] = {}
                LSPK_CONFIG["outputs"][1] = make_paudio_output( 'fr.L' )
                LSPK_CONFIG["outputs"][2] = make_paudio_output( 'fr.R' )
                return


            # Outputs
            for out, params in LSPK_CONFIG["outputs"].items():

                # It is expected 4 fields
                params = params.split() if params else []
                params += [''] * (4 - len(params))

                # Redo in dictionary form
                if not any(params):
                    params = make_paudio_output('')

                else:
                    _, p = check_output_params(out, params)
                    name, gain, pol, delay = p
                    params = make_paudio_output(name, gain, pol, delay)

                LSPK_CONFIG["outputs"][out] = params

            # Check L/R pairs
            check_output_names()


        # Load lspk.yml
        LSPK_CONFIG = load_lspk_config()

        # Complete filter syntax from the simplified syntax in lspk.yml
        populate_lspk_eq_filters()
        populate_xo_filters()
        populate_drc_filters()

        # Converting the Human Readable 'outputs:' section to a dictionary
        reformat_outputs()

        return LSPK_CONFIG


    global CONFIG, LOUDSPEAKER, LSPKFOLDER

    CONFIG = yaml.safe_load( open(CONFIG_PATH, 'r') )
    CONFIG["mainfolder"] = MAINFOLDER

    #
    # Default values if omited parameters
    #
    if not "samplerate" in CONFIG:
        CONFIG["samplerate"] = 44100
        print(f'{Fmt.BOLD}\n!!! samplerate NOT configured, default to fs=44100\n{Fmt.END}')

    if not CONFIG.get("plugins"):
        CONFIG["plugins"] = []

    if not 'sources' in CONFIG:
        CONFIG["sources"] = {'system-wide':{}}
    else:
        CONFIG["sources"]["none"] = {}

    if not 'ref_level_gain_offset' in CONFIG:
        CONFIG["ref_level_gain_offset"] = 0.0

    if not "tones_span_dB" in CONFIG:
        CONFIG["tones_span_dB"] = 6.0

    if CONFIG.get('loudspeaker'):
        LOUDSPEAKER = CONFIG["loudspeaker"]
    else:
        LOUDSPEAKER = 'generic_loudspeaker'
        CONFIG["loudspeaker"] = LOUDSPEAKER

    LSPKFOLDER = f'{LSPKSFOLDER}/{LOUDSPEAKER}'
    if not os.path.isdir(LSPKFOLDER):
        os.mkdir(LSPKFOLDER)
    if not os.path.isdir(f'{LSPKFOLDER}/{CONFIG["samplerate"]}'):
        os.mkdir(f'{LSPKFOLDER}/{CONFIG["samplerate"]}')

    LSPK_YML_PATH = f'{LSPKFOLDER}/lspk.yml'


    # MERGING the specific LOUDSPEAKER configuration
    lspk_config = get_lspk_config()
    #
    # DEBUG
    #print('--- lspk.yml ----')
    #print( yaml.dump(lspk_config, default_flow_style=False, sort_keys=False, indent=2) )
    #

    # 1. Loudspeaker multiway:

    # 1.a. Sound card outputs:
    CONFIG["outputs"] = lspk_config["outputs"]

    # 1.b. Loudspeaker XO:
    CONFIG["xo"] = {}
    if lspk_config.get('xo'):
        CONFIG["xo"] = lspk_config["xo"]
    if lspk_config.get('xo_gains'):
        CONFIG["xo_gains"] = lspk_config["xo_gains"]

    # 2. Loudspeaker EQ:
    CONFIG["lspk_eq"] = {}
    if lspk_config.get('lspk_eq'):
        CONFIG["lspk_eq"] = lspk_config["lspk_eq"]
    CONFIG["lspk_eq_safe_gain"] = lspk_config.get('lspk_eq_safe_gain', 0.0)

    # 3. Loudspeaker DRC:
    CONFIG["drc"] = {}
    if lspk_config.get('drc'):
        CONFIG["drc"] = lspk_config["drc"]

    # Dump to disk for maintenence
    pAudio_cfg_json_path = f'{LOGFOLDER}/.pAudio_cfg'
    with open(pAudio_cfg_json_path, 'w') as f:
        f.write( yaml.dump(CONFIG, default_flow_style=False, sort_keys=False, indent=2) )

    # DEBUG
    #print('--- pAudio ----')
    #print(CONFIG.keys())
    #print( yaml.dump(CONFIG, default_flow_style=False, sort_keys=False, indent=2) )


_init()
