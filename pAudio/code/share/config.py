#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  sys
import  os
import  yaml
from    fmt                     import Fmt
from    pcamilla_mod.do_makes   import *

UHOME = os.path.expanduser('~')
MAINFOLDER              = f'{UHOME}/pAudio'

LSPKSFOLDER             = f'{MAINFOLDER}/loudspeakers'
LSPKFOLDER              = f''
LOUDSPEAKER             = f''   # to be found later
LSPK_YML_PATH           = f''   #

EQFOLDER                = f'{MAINFOLDER}/eq'
CODEFOLDER              = f'{MAINFOLDER}/code'
CONFIG_PATH             = f'{MAINFOLDER}/config.yml'
LOGFOLDER               = f'{MAINFOLDER}/log'
PLUGINSFOLDER           = f'{MAINFOLDER}/code/share/plugins'
MACROSFOLDER            = f'{MAINFOLDER}/code/macros'

PREAMP_STATE_PATH       = f'{MAINFOLDER}/.preamp_state'
LDCTRL_PATH             = f'{MAINFOLDER}/.loudness_control'
LDMON_PATH              = f'{MAINFOLDER}/.loudness_monitor'
AUXINFO_PATH            = f'{MAINFOLDER}/.aux_info'

PLAYER_INFO_PATH        = f'{MAINFOLDER}/.player_info'
PLAYERTEMPLATE = {
    'player':       '',
    'state':        '',
    'time_pos':     '',
    'time_tot':     '',
    'bitrate':      '',
    'artist':       '',
    'album':        '',
    'title':        '',
    'track_num':    '',
    'track_uri':    '',
    'tracks_tot':   ''
}

CDDA_MUSICBRAINZ_PATH   = f'{MAINFOLDER}/.cdda_musicbrainz'
CDDA_META_PATH          = f'{MAINFOLDER}/.cdda_metadata'
CDDA_META_TEMPLATE = {
    'discid':   '',
    'artist':   '',
    'album':    '',
    'tracks':   { }
}

AMP_STATE_PATH      = f'{UHOME}/.amplifier'


def find_key_value(data, key, value):
    """ search recursively for 'key':value to exist in the given data
    """

    if isinstance(data, dict):
        for k, v in data.items():
            if k == key and v == value:
                return True
            if find_key_value(v, key, value):
                return True

    elif isinstance(data, list):
        for item in data:
            if find_key_value(v, key, value):
                return True

    return False


def _init():

    def complete_jack_params():

        if not 'device' in CONFIG["jack"] or not CONFIG["jack"]["device"]:
            print(f'{Fmt.BOLD}BAD Jack config{Fmt.END}')
            sys.exit()

        period   = CONFIG["jack"].get('period', 1024)
        nperiods = CONFIG["jack"].get('nperiods', 2)
        dither   = CONFIG["jack"].get('dither', False)
        softmode = CONFIG["jack"].get('softmode', False)

        CONFIG["jack"]["period"]    = period
        CONFIG["jack"]["nperiods"]  = nperiods
        CONFIG["jack"]["dither"]    = dither
        CONFIG["jack"]["softmode"]  = softmode

        tmp = CONFIG["jack"].get('zita_udp_base', None)

        if type(tmp) != int:
            CONFIG["jack"]["zita_udp_base"] = 65000
            if tmp:
                print(f'{Fmt.RED}(config) Bad value zita_udp_base: {tmp}, using 65000{Fmt.END}')

        tmp = CONFIG["jack"].get('zita_buffer_ms', None)

        if type(tmp) != int:
            CONFIG["jack"]["zita_buffer_ms"] = 20
            if tmp:
                print(f'{Fmt.RED}(config) Bad value zita_buffer_ms: {tmp}, using 20{Fmt.END}')


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
                        if CONFIG["verbose"]:
                            print(f'{Fmt.BLUE}Loudspeaker config file `{CONFIG["loudspeaker"]}/lspk.yml` was found{Fmt.END}')

                except Exception as e:
                    print(f'{Fmt.RED}Cannot load {CONFIG["loudspeaker"]}/lspk.yml {str(e)}{Fmt.END}')


            if find_key_value(res, 'type', 'fir'):
                print(f'{Fmt.BOLD}(config.py) FLOAT32 is assumed for the FIR filters{Fmt.END}')

            return res


        def populate_lspk_eq_filters():
            """ currently lspk_eq filters are assumed to be in CamillaDSP format
            """
            pass


        def populate_drc_filters():
            """ - FIR have only the drc-set-name as values, so we need
                  to REPLACE it with the whole parameters for both channels.

                - IIR is assumed to have a regular complete filter syntax,
                  usually imported from Room Equalizer Wizard aka REW,
                  so nothing is done but gains fields.

                Also will prepare an auxiliary CamillaDSP filter definition
                for gain on each xo-set-name-way
            """

            if not 'drc' in LSPK_CONFIG or not LSPK_CONFIG.get('drc'):
                return

            LSPK_CONFIG["drc_gains"] = {}

            for set_name, values in LSPK_CONFIG.get('drc', {}).items():

                # FIR
                if values.get('type', '') == 'fir':

                    fs = CONFIG["samplerate"]

                    # prepare channels syntax and save gains
                    channels = { 'L': {}, 'R': {} }

                    for ch in channels.keys():

                        fir_path = f'{LSPKFOLDER}/{fs}/drc.{ch}.{set_name}.pcm'

                        channels[ch][1] = make_fir_filter(fir_path)

                    LSPK_CONFIG["drc"][set_name] = channels

                # IIR
                else:
                    pass

                LSPK_CONFIG["drc_gains"][set_name] = { 'flat_gain':     values.pop('flat_gain',  0.0),
                                                       'posit_gain':    values.pop('posit_gain', 0.0)
                                                     }


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

                    LSPK_CONFIG["xo_gains"][f'{way}.{set_name}'] = { 'flat_gain':     params.pop('flat_gain',  0.0),
                                                                     'posit_gain':    params.pop('posit_gain', 0.0)
                                                                    }


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


    global PAUDIO_ADDR, PAUDIO_PORT, CAMILLADSP_PORT, \
           CONFIG, LOUDSPEAKER, LSPKFOLDER


    CONFIG = yaml.safe_load( open(CONFIG_PATH, 'r') )

    CONFIG["verbose"] = False
    try:
        with open(f'{MAINFOLDER}/.verbose', 'r') as f:
            tmp = f.read()
            if 'true' in tmp.lower():
                CONFIG["verbose"] = True
    except:
        pass

    # prepare LOG folder
    if not os.path.isdir(LOGFOLDER):
        os.mkdir(LOGFOLDER)

    # Default addressing unless config.yml
    PAUDIO_ADDR     = CONFIG.get('paudio_addr',     '0.0.0.0')
    PAUDIO_PORT     = CONFIG.get('paudio_port',     9990)
    CAMILLADSP_PORT = CONFIG.get('camilladsp_port', 1234)

    # CamillaDSP activation wait (default 0.1 s)
    # If you experience problems with CamillaDSP on JACK in slow machines, like
    #     BDB2034 unable to allocate memory for mutex; resize mutex region
    # then slightly increase this value under pAudio/config.yml.
    CONFIG['camilladsp_activation_wait'] = CONFIG.get('camilladsp_activation_wait', 0.1)


    if "jack" in CONFIG:
        complete_jack_params()

    if not "samplerate" in CONFIG:
        CONFIG["samplerate"] = 44100
        print(f'{Fmt.BOLD}\n!!! samplerate NOT configured, default to fs=44100\n{Fmt.END}')

    if not CONFIG.get("plugins"):
        CONFIG["plugins"] = []

    if not 'sources' in CONFIG:
        if CONFIG.get('jack'):
            CONFIG["sources"] = {'system-wide':{}}
        else:
            CONFIG["sources"] = {'Desktop':{}}
    else:
        # add a none source
        CONFIG["sources"]["none"] = {}

    if not 'ref_level_gain_offset' in CONFIG:
        CONFIG["ref_level_gain_offset"] = 0.0

    if not 'loudness_compensation_clamped_above_zero' in CONFIG:
        CONFIG["loudness_compensation_above_zero"] = False

    if not "tones_span_dB" in CONFIG:
        CONFIG["tones_span_dB"] = 6.0

    if not "compressors" in CONFIG:
        CONFIG["compressors"] = ['1.0:1', '2.0:1', '3.0:1']
    if not 'off' in CONFIG["compressors"]:
        CONFIG["compressors"].insert(0, 'off')

    #-----------------------------------------------
    # Expert zone
    if not CONFIG.get('expert_zone', {}):
        CONFIG['expert_zone'] = {}

    if CONFIG.get('expert_zone', {}).get('camilladsp_xrun_monitor', None) == None:
        CONFIG["expert_zone"]["camilladsp_xrun_monitor"] = False

    #-----------------------------------------------
    # LOUDSPEAKER configuration will be merged below.
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

    CONFIG["lspk_eq_posit_gain"] = lspk_config.get('lspk_eq_posit_gain', 0.0)

    # 3. Loudspeaker DRC:
    CONFIG["drc"] = {}

    if lspk_config.get('drc'):
        CONFIG["drc"] = lspk_config["drc"]

    if lspk_config.get('drc_gains'):
        CONFIG["drc_gains"] = lspk_config["drc_gains"]

    # DEBUG
    #print('--- pAudio ----')
    #print(CONFIG.keys())
    #print( yaml.dump(CONFIG, default_flow_style=False, sort_keys=False, indent=2) )


_init()
