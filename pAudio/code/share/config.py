#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  os
import  yaml

UHOME = os.path.expanduser('~')

MAINFOLDER          = f'{UHOME}/pAudio'
LSPKSFOLDER         = f'{MAINFOLDER}/loudspeakers'
LSPKFOLDER          = f''
LOUDSPEAKER         = f''   # to be found when loading CONFIG
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

CONFIG = {}


def _init():

    def combine_lspk_config():
        """ This merges the BASE YML and the LOUDSPEAKER YML

            returns True if the loudspeaker uses CamillaDSP
        """

        def get_lspk_config():
            """ retunrs void {} if not found a loudspeaker's CamillaDSP yml file
            """

            lspk = CONFIG["loudspeaker"]

            lspk_camilla_yml_path = f'{MAINFOLDER}/loudspeakers/{lspk}/camilladsp_lspk.yml'

            try:
                with open(lspk_camilla_yml_path, 'r') as f:
                    cfg = yaml.safe_load( f.read() )
                print(f'{Fmt.BLUE}Loudspeaker {lspk}/camilladsp.yml was found{Fmt.END}')
                return cfg

            except Exception as e:
                print(f'{Fmt.BLUE}Cannot load {lspk}/camilladsp_lspk.yml {str(e)}{Fmt.END}')
                return {}


        lspk = CONFIG["loudspeaker"]

        lspk_uses_cdsp = False

        # Loading the base config
        with open(BASE_YML_PATH, 'r') as f:
            base_config = yaml.safe_load( f.read() )

        # Prepare the runtime config
        runtime_config = base_config

        # Getting and merging the loudspeaker config
        lspk_config = get_lspk_config()

        # merging filters
        if 'filters' in lspk_config:

            lspk_uses_cdsp = True

            runtime_config["filters"] = lspk_config["filters"]

            # Pipeline step for loudspeaker EQ filters (will be applied at both channels)
            pipeline_eq_L_step = {
                'type':         'Filter',
                'description':  f'{lspk} (EQ left)',
                'channels':     [0],
                'bypassed':     False,
                'names':        []
            }
            pipeline_eq_R_step = {
                'type':         'Filter',
                'description':  f'{lspk} (EQ right)',
                'channels':     [1],
                'bypassed':     False,
                'names':        []
            }
            pipeline_eq_L_step_names = []
            pipeline_eq_R_step_names = []


            # Pipeline step for loudspeaker DRC filters
            pipeline_drc_L_step = {
                'type':         'Filter',
                'description':  f'{lspk} (DRC left)',
                'channels':     [0],
                'bypassed':     False,
                'names':        []
            }
            pipeline_drc_R_step = {
                'type':         'Filter',
                'description':  f'{lspk} (DRC right)',
                'channels':     [1],
                'bypassed':     False,
                'names':        []
            }
            pipeline_drc_L_step_names = []
            pipeline_drc_R_step_names = []

            # Iterate over loudspeaker filters
            for f in lspk_config["filters"]:

                # Filter is common for both channels
                if not '_L_' in f and not '_R_' in f:

                    pipeline_eq_L_step_names.append(f)
                    print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_L_step["description"]}`{Fmt.END}')
                    pipeline_eq_R_step_names.append(f)
                    print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_R_step["description"]}`{Fmt.END}')

                # Filter is for an specific channel (i.e. DRC)
                else:

                    if '_L_' in f:
                        pipeline_drc_L_step_names.append(f)
                        print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_drc_L_step["description"]}`{Fmt.END}')

                    if '_R_' in f:
                        pipeline_drc_R_step_names.append(f)
                        print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_drc_R_step["description"]}`{Fmt.END}')

            pipeline_eq_L_step["names"] = pipeline_eq_L_step_names
            pipeline_eq_R_step["names"] = pipeline_eq_R_step_names

            pipeline_drc_L_step["names"] = pipeline_drc_L_step_names
            pipeline_drc_R_step["names"] = pipeline_drc_R_step_names

            if pipeline_eq_L_step["names"] :
                runtime_config["pipeline"].append( pipeline_eq_L_step )
                runtime_config["pipeline"].append( pipeline_eq_R_step )

            if pipeline_drc_L_step["names"] :
                runtime_config["pipeline"].append( pipeline_drc_L_step )
                runtime_config["pipeline"].append( pipeline_drc_R_step )


        # Setting the safe gain if required:
        safe_gain = 0
        if 'safe_gain' in lspk_config and lspk_config["safe_gain"]:
            safe_gain = lspk_config["safe_gain"]

        # Write runtime configuration in the final YAML file for CamillaDSP to start
        with open(RUNTIME_YML_PATH, 'w') as f:
            yaml.dump(runtime_config, f, default_flow_style=False)

        return lspk_uses_cdsp, safe_gain


    def reformat_PEQ():
        """ PEQa are given in NON standard YML, having 3 fields. Example:

            PEQ:
                L:
                    #   freq    gain    Q
                    1:  123     -2.0    1.0
                    2:  456     -3.0    0.5
                R:
                    ...

            Here will convert the Human Readable fields into a dictionary.
        """

        def check_peq_params(params):

            freq, gain, q = params

            freq = float(freq)
            gain = float(gain)
            q    = float(q)

            if freq < 20.0 or freq > 20e3:
                raise Exception('Freq must be 20 ~ 20000 (Hz)')

            if gain < -20 or gain > 6:
                raise Exception('Gain must be in -20.0 ~ +6.0 (dB)')

            if q < 0.1 or q > 10:
                raise Exception('Q must be in 0.1 ~ 10')

            return freq, gain, q


        # Filling the empty keys
        if not 'PEQ' in CONFIG or not CONFIG["PEQ"]:
            CONFIG["PEQ"] = {'L': {}, 'R': {}}
        if not 'L' in CONFIG["PEQ"]:
            CONFIG["PEQ"]["L"] = {}
        if not 'R' in CONFIG["PEQ"]:
            CONFIG["PEQ"]["R"] = {}

        # PEQ parameters
        for ch in CONFIG["PEQ"]:

            if not ch in ('L', 'R'):
                raise Exception('PEQ channel must be `L` or `R`')

            if not CONFIG["PEQ"][ch]:
                CONFIG["PEQ"][ch] = {}

            for peq, params in CONFIG["PEQ"][ch].items():

                # It is expected 3 fields
                params = params.split()
                if len(params) != 3:
                    raise Exception(f'Bad PEQ #{peq}')

                # Redo in dictionary form
                freq, gain, q = check_peq_params(params)
                params = {  'freq':     freq,
                            'gain':     gain,
                            'q':        q       }

                CONFIG["PEQ"][ch][peq] = params


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
            outputs = CONFIG["outputs"]

            L_outs  = [ pms["name"] for o, pms in outputs.items()
                        if pms["name"] and pms["name"][-1]=='L' ]
            R_outs  = [ pms["name"] for o, pms in outputs.items()
                        if pms["name"] and pms["name"][-1]=='R' ]

            if len(L_outs) != len(R_outs):
                raise Exception('Number of outputs for L and R does not match')


        # A simple stereo I/O configuration if not defined
        if not 'outputs' in CONFIG:
            CONFIG["outputs"] = {1: 'fr.L', 2: 'fr.R'}

        # Outputs
        for out, params in CONFIG["outputs"].items():

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

            CONFIG["outputs"][out] = params

        # Check L/R pairs
        check_output_names()


    global CONFIG, LOUDSPEAKER, LSPKFOLDER

    CONFIG = yaml.safe_load( open(CONFIG_PATH, 'r') )


    if 'loudspeaker' in CONFIG:
        LOUDSPEAKER = CONFIG["loudspeaker"]
    else:
        LOUDSPEAKER = 'generic_loudspk'
        CONFIG["loudspeaker"] = LOUDSPEAKER

    LSPKFOLDER = f'{LSPKSFOLDER}/{LOUDSPEAKER}'
    if not os.path.isdir(LSPKFOLDER):
        os.mkdir(LSPKFOLDER)

    #
    # Default values if omited parameters
    #
    if not "samplerate" in CONFIG:
        CONFIG["samplerate"] = 44100
        print(f'{Fmt.BOLD}\n!!! samplerate NOT configured, default to fs=44100\n{Fmt.END}')

    if not "plugins" in CONFIG or not CONFIG["plugins"]:
        CONFIG["plugins"] = []

    if not 'inputs' in CONFIG:
        CONFIG["inputs"] = {'system-wide':{}}
    else:
        CONFIG["inputs"]["none"] = {}

    if not 'drcs_offset' in CONFIG:
        CONFIG["drcs_offset"] = 0.0

    if not 'ref_level_gain_offset' in CONFIG:
        CONFIG["ref_level_gain_offset"] = 0.0

    if not "tones_span_dB" in CONFIG:
        CONFIG["tones_span_dB"] = 6.0


    #lspk_uses_camilladsp, global_volume = combine_lspk_config()

    # Converting the Human Readable outputs section to a dictionary
    reformat_outputs()

    # Converting the Human Readable PEQ section to a dictionary
    reformat_PEQ()


_init()
