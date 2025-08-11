#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  sys
import  os
import  yaml
from    fmt         import Fmt

UHOME = os.path.expanduser('~')
MAINFOLDER          = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/services/preamp_mod/pcamilla_mod')

import do_makes


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
            - try to load a loudspeaker's CamillaDSP YAML file

            - if outputs: section is NOT defined, defaults to an stereo ones

        """

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


            # Outputs
            for out, params in LSPK_CONFIG["outputs"].items():

                # It is expected 4 fields
                params = params.split() if params else []
                params += [''] * (4 - len(params))

                # Redo in dictionary form
                if not any(params):
                    params = {  'name':     '',
                                'gain':     0.0,
                                'polarity': '+',
                                'delay':    0.0     }

                else:
                    _, p = check_output_params(out, params)
                    name, gain, pol, delay = p
                    params = {  'name':     name,
                                'gain':     gain,
                                'polarity': pol,
                                'delay':    delay   }

                LSPK_CONFIG["outputs"][out] = params


            # Check L/R pairs
            check_output_names()


        def populate_fir_xo(set_name):
            """ FIR XO under camilladsp_lspk.yml 'xo:' section has only the name of a PCM set
                This will replace that value with a complete filter set syntax
            """

            def get_xo_pcm_names_from_loudspeaker_folder():
                """ looks for xo.xxxx.pcm files inside the loudspeaker folder
                """
                xo_files    = []
                xo_filters  = []

                LSPKFOLDER_FS = f'{LSPKFOLDER}/{CONFIG["samplerate"]}'

                try:
                    files = os.listdir(LSPKFOLDER_FS)
                    files = [x for x in files if os.path.isfile(f'{LSPKFOLDER_FS}/{x}') ]
                    xo_files = [x for x in files if x.startswith('xo.')
                                                    and
                                                    x.endswith('.pcm')]
                except Exception as e:
                    print(f'{Fmt.BOLD}get_xo_filters_from_loudspeaker_folder ERROR: {str(e)}{Fmt.END}')

                for f in xo_files:
                    xo_id = f.replace('xo.', '').replace('.pcm', '')
                    xo_filters.append(xo_id)

                # something like ['lo.lp.original', 'lo.mp.original', 'hi.mp.original', 'hi.lp.original']

                return xo_filters


            result = {}

            pcm_names = get_xo_pcm_names_from_loudspeaker_folder()
            # example: ['lo.original.mp', 'hi.original.mp', 'lo.original.lp', 'hi.original.lp']

            pcm_names = [x for x in pcm_names if set_name in x]
            # example: set_name 'original.mp' --> ['lo.original.mp', 'hi.original.mp']

            for pcm_name in pcm_names:
                way = pcm_name[:2]
                result[way] = do_makes.make_xo_fir_filter(pcm_name, CONFIG["samplerate"], LSPKFOLDER)

            return result


        def populate_iir_xo(set_name, values):
            """ IIR XO under camilladsp_lspk.yml 'xo:' section has only a few parameters. Example:

                    set_name:   'myxo'

                    values:
                                lo:
                                    type:   LR
                                    order:  2
                                    freq:   2000
                                hi:
                                    type:   LR
                                    order:  2
                                    freq:   2000

                This will replace that values with a complete filter set syntax
            """
            result = {}

            for way, params in values.items():
                result[way] = do_makes.make_xo_iir_filter(way, params["type"], params["order"], params["freq"])

            return result


        LSPK_CONFIG = {}

        if os.path.isfile(LSPK_YML_PATH):

            try:
                with open(LSPK_YML_PATH, 'r') as f:
                    LSPK_CONFIG = yaml.safe_load( f.read() )
                print(f'{Fmt.BLUE}Loudspeaker {CONFIG["loudspeaker"]}/camilladsp_lspk.yml was found{Fmt.END}')

            except Exception as e:
                print(f'{Fmt.RED}Cannot load {CONFIG["loudspeaker"]}/camilladsp_lspk.yml {str(e)}{Fmt.END}')


        # DEFAULT FULL RANGE LOUDSPEAKER OUTPUTs
        if not LSPK_CONFIG.get("outputs"):
            LSPK_CONFIG["outputs"] = {1: 'fr.L', 2: 'fr.R'}

        # Converting the Human Readable 'outputs:' section to a dictionary
        reformat_outputs()

        # Populate XO filters if any
        if 'xo' in LSPK_CONFIG and LSPK_CONFIG.get('xo'):

            for set_name, values in LSPK_CONFIG["xo"].items():

                # FIR xo
                if type(values) == str and values == 'fir':
                    LSPK_CONFIG["xo"][set_name] = populate_fir_xo(set_name)

                # IIR xo
                else:
                    LSPK_CONFIG["xo"][set_name] = populate_iir_xo(set_name, values)

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

    if not 'drcs_offset' in CONFIG:
        CONFIG["drcs_offset"] = 0.0

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

    LSPK_YML_PATH = f'{LSPKFOLDER}/camilladsp_lspk.yml'


    # MERGING the specific LOUDSPEAKER YAML configuration
    lspk_config = get_lspk_config()
    #
    # DEBUG
    #print('--- camilladsp_lspk.yml ----')
    #print( yaml.dump(lspk_config, default_flow_style=False, sort_keys=False, indent=2) )
    #

    # 1. Loudspeaker multiway:

    # 1.a. Sound card outputs:
    CONFIG["outputs"] = lspk_config["outputs"]

    # 1.b. Loudspeaker XO
    CONFIG["xo"] = lspk_config["xo"]

    # 2. Loudspeaker EQ:
    if not CONFIG.get('lspk_eq'):
        CONFIG["lspk_eq"] = {}

    if lspk_config.get('lspk_eq'):
        for fname, fparams in lspk_config["lspk_eq"].items():
            CONFIG["lspk_eq"][fname] = fparams

    # 3. Loudspeaker DRC:
    if lspk_config.get('drc'):
        CONFIG["drc"] = lspk_config["drc"]
    else:
        CONFIG["drc"] = {}

    # Dump to disk for maintenence
    pAudio_cfg_json_path = f'{LOGFOLDER}/.pAudio_cfg'
    with open(pAudio_cfg_json_path, 'w') as f:
        f.write( yaml.dump(CONFIG, default_flow_style=False, sort_keys=False, indent=2) )

    # DEBUG
    #print('--- pAudio ----')
    #print(CONFIG.keys())
    #print( yaml.dump(CONFIG, default_flow_style=False, sort_keys=False, indent=2) )


_init()
