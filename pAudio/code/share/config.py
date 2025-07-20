#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  os
import  yaml
from    fmt     import Fmt

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

    def get_lspk_config():
        """ retunrs void {} if not found a loudspeaker's CamillaDSP yml file
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
                outputs = LSPK_CGF["outputs"]

                L_outs  = [ pms["name"] for o, pms in outputs.items()
                            if pms["name"] and pms["name"][-1]=='L' ]
                R_outs  = [ pms["name"] for o, pms in outputs.items()
                            if pms["name"] and pms["name"][-1]=='R' ]

                if len(L_outs) != len(R_outs):
                    raise Exception('Number of outputs for L and R does not match')


            # A simple stereo I/O configuration if not defined
            if not 'outputs' in LSPK_CGF:
                LSPK_CGF["outputs"] = {1: 'fr.L', 2: 'fr.R'}

            # Outputs
            for out, params in LSPK_CGF["outputs"].items():

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

                LSPK_CGF["outputs"][out] = params


            # Check L/R pairs
            check_output_names()


        LSPK_CGF = {}

        lspk = CONFIG["loudspeaker"]

        lspk_camilla_yml_path = f'{MAINFOLDER}/loudspeakers/{lspk}/camilladsp_lspk.yml'

        try:
            with open(lspk_camilla_yml_path, 'r') as f:
                LSPK_CGF = yaml.safe_load( f.read() )
            print(f'{Fmt.BLUE}Loudspeaker {lspk}/camilladsp_lspk.yml was found{Fmt.END}')

        except Exception as e:
            print(f'{Fmt.RED}Cannot load {lspk}/camilladsp_lspk.yml {str(e)}{Fmt.END}')


        # Converting the Human Readable outputs section to a dictionary
        reformat_outputs()

        return LSPK_CGF


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


    # Converting the Human Readable PEQ section under CONFIG to a dictionary
    reformat_PEQ()

    # Merging the specific LOUDSPEAKER configuration into CONFIG
    lspk_config = get_lspk_config()
    #
    # outputs:
    CONFIG["outpus"] = lspk_config["outputs"]
    #
    # eq:
    # TODO

    # DEBUG
    #print( yaml.dump(CONFIG, default_flow_style=False, sort_keys=False, indent=2) )


_init()
