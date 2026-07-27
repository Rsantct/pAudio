#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  sys
import  os
from    time                    import time
import  numpy as np
import  yaml
import  json
from    fmt                     import Fmt
from    pcamilla_mod.do_makes   import *

UHOME = os.path.expanduser('~')
MAINFOLDER          = f'{UHOME}/pAudio'

LSPKSFOLDER         = f'{MAINFOLDER}/loudspeakers'
LSPKFOLDER          = f''
LOUDSPEAKER         = f''   # to be found later

EQFOLDER            = f'{MAINFOLDER}/eq'
CODEFOLDER          = f'{MAINFOLDER}/code'
CONFIG_PATH         = f'{MAINFOLDER}/config/config.yml'
LOGFOLDER           = f'{MAINFOLDER}/log'
PLUGINSFOLDER       = f'{MAINFOLDER}/code/share/plugins'
MACROSFOLDER        = f'{MAINFOLDER}/macros'

PREAMP_STATE_PATH   = f'{MAINFOLDER}/.preamp_state'
LDCTRL_PATH         = f'{MAINFOLDER}/.loudness_control'
LDMON_PATH          = f'{MAINFOLDER}/.loudness_monitor'
AUXINFO_PATH        = f'{MAINFOLDER}/.aux_info'
PAUDIO_CFG_PATH     = f'{LOGFOLDER}/pAudio_cfg'
AMP_STATE_PATH      = f'{UHOME}/.amplifier'

PLAYER_INFO_PATH    = f'{MAINFOLDER}/.player_info'
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

CDDA_MUSICBRAINZ_PATH = f'{MAINFOLDER}/.cdda_musicbrainz'
CDDA_META_PATH        = f'{MAINFOLDER}/.cdda_metadata'
CDDA_META_TEMPLATE = {
    'discid':   '',
    'artist':   '',
    'album':    '',
    'tracks':   { }
}


def write_pAudio_cfg(data):
    with open(PAUDIO_CFG_PATH, 'w') as f:
        f.write( json.dumps(data, indent=2) )


def read_pAudio_cfg():
    with open(PAUDIO_CFG_PATH, 'r') as f:
        c = json.loads( f.read() )
    return c


def pAudio_cfg_is_recent(seconds_old=30):

    if os.path.exists(PAUDIO_CFG_PATH):
        mtime = os.path.getmtime(PAUDIO_CFG_PATH)
        now = time()
        if (now - mtime) < seconds_old:
            return True

    return False


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


def complete_config():

    def prepare_coreaudio_init_devices():
        """
        (i) THERE ARE TWO syntax options for Coreaudio capture device(s):

        coreaudio:

            devices:

                capture:

                    ---------------------------------------------------------------
                    Normal coreaudio input device directly specified:

                    channels: 2
                    device: BlackHole 2ch
                    format: F32_LE


                    ---------------------------------------------------------------
                    Alternative more than one section, to have source selection

                    Mac Desktop:
                        channels: 2
                        device: BlackHole 2ch
                        format: F32_LE

                    TV:
                        channels: 2
                        device: UMC204HD 192k
                        format: S24_3_LE
                    ---------------------------------------------------------------


                playback:

                    channels: 2
                    device: Altavoces del MacBook Pro
                    format: F32_LE

        --> If the ALTERNATIVE syntax was used, we complete the normal syntax here,
            taking the first device found.

        """


        # If 'alternative' syntax was used,
        # we need to generate a 'normal' capture section
        if not CONFIG["coreaudio"]["devices"]["capture"].get('device'):

            in_devices = CONFIG["coreaudio"]["devices"].get('capture')

            _first_in_device, first_in_device_params = next( iter( in_devices.items() ) )

            # Adding the 'normal' capture section
            CONFIG["coreaudio"]["devices"]["capture"] = first_in_device_params


    def complete_jack_params():

        if not 'device' in CONFIG["jack"] or not CONFIG["jack"]["device"]:
            print(f'{Fmt.BOLD}(config) BAD Jack config{Fmt.END}')
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
            CONFIG["jack"]["zita_buffer_ms"] = 10
            if tmp:
                print(f'{Fmt.RED}(config) Bad value zita_buffer_ms: {tmp}, using 10{Fmt.END}')


    def get_lspk_config():
        """
            - Read the loudspeaker's YAML file

            - Some sections can have simplified filter definitions,
              here will populate a complete CamillaDSP filter syntax

            - If outputs: section is NOT defined, defaults to an stereo ones

        """

        def get_fir_latency(fir_path):
            """ Analize FIR latency

                Example of xover PCM files:

                    .../my_lspk/44100/xo.lo.set_name.pcm
                    .../my_lspk/44100/xo.hi.set_name.pcm
            """

            def readPCM(fname, dtype=np.float32):
                return np.fromfile(fname, dtype=dtype)


            def get_peak(fir):
                peak_pos = np.argmax(np.abs(fir))
                fs = CONFIG['samplerate']
                latency_ms = round(peak_pos / fs * 1000, 1)
                return (latency_ms, peak_pos)

            if not os.path.isfile(fir_path):
                return f'not found: {fir_path}'

            fir = readPCM( str(fir_path) )
            latency, _ = get_peak(fir)

            return latency


        def load_lspk_config():

            res = {}

            lspk_yml_path = f'{LSPKFOLDER}/lspk.yml'
            if os.path.isfile(lspk_yml_path):

                try:
                    with open(lspk_yml_path, 'r') as f:
                        res = yaml.safe_load( f.read() )
                        if CONFIG["verbose"]:
                            print(f'{Fmt.BLUE}(config) Loudspeaker config file `{CONFIG["loudspeaker"]}/lspk.yml` was found{Fmt.END}')

                except Exception as e:
                    print(f'{Fmt.RED}(config) Cannot load {CONFIG["loudspeaker"]}/lspk.yml {str(e)}{Fmt.END}')


            if find_key_value(res, 'type', 'fir'):
                print(f'{Fmt.RED}{Fmt.ITALIC}(config) FLOAT32 is assumed for raw pcm FIR files{Fmt.END}')

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
            """

            if not 'drc' in LSPK_CONFIG or not LSPK_CONFIG.get('drc'):
                return

            for set_name, values in LSPK_CONFIG.get('drc', {}).items():

                # FIR
                if values.get('type', '') == 'fir':

                    fs = CONFIG["samplerate"]

                    # prepare channels syntax and save gains
                    channels = { 'L': {}, 'R': {} }

                    for ch in channels.keys():

                        fir_path = f'{LSPKFOLDER}/{fs}/drc.{ch}.{set_name}.pcm'

                        if os.path.isfile(fir_path):
                            channels[ch][1] = make_fir_filter(fir_path)
                        else:
                            raise Exception (f'DRC set file not found: {fir_path}')

                    LSPK_CONFIG["drc"][set_name] = channels

                # IIR
                else:
                    pass

                LSPK_CONFIG["drc"][set_name]["flat_gain"]  = values.get('flat_gain',  0.0)
                LSPK_CONFIG["drc"][set_name]["posit_gain"] = values.get('posit_gain', 0.0)


        def populate_xo_filters():
            """ XO items in lspk.yml comes in a human readable format,
                here we complete a CamillaDSP syntax for them.

                Also will prepare an auxiliary CamillaDSP filter definition
                for gain on each xo-set-name-way
            """

            if not 'xo' in LSPK_CONFIG or not LSPK_CONFIG.get('xo'):
                return

            for set_name, ways in LSPK_CONFIG["xo"].items():

                for way, params in ways.items():

                    # FIR
                    if params.get('type') == 'fir':
                        fir_path = f'{LSPKFOLDER}/{CONFIG["samplerate"]}/xo.{way}.{set_name}.pcm'
                        LSPK_CONFIG["xo"][set_name][way] = make_fir_filter( fir_path )
                        LSPK_CONFIG["xo"][set_name][way]["parameters"]["latency"] = get_fir_latency( fir_path )


                    # IIR
                    else:
                        ftype, order, freq = params["type"], params["order"], params["freq"]
                        LSPK_CONFIG["xo"][set_name][way] = make_xo_iir_filter(way, ftype, order, freq)
                        LSPK_CONFIG["xo"][set_name][way]["parameters"]["latency"] = 0.0

                    LSPK_CONFIG["xo"][set_name][way]["parameters"]["flat_gain"]  = params.get('flat_gain',  0.0)
                    LSPK_CONFIG["xo"][set_name][way]["parameters"]["posit_gain"] = params.get('posit_gain', 0.0)


        def reformat_outputs():
            """
                outputs section is given in NON standard YML, having 5 fields.

                Valid names are:

                    fullrange:  fr.L, fr.R
                    xover:      [lo|mi|hi].[L|R]  (example: 'lo.L', 'hi.R')
                    subwoofer:  sw

                A void section will default to a basic fr.L + fr.L mapping

                Example of 2 way stereo by using the physical sound card ports
                as well other extra outputs:

                outputs:

                    # (i) Output numbers greater than the available sound card ports
                    #     (jackd system:playback_N ) will be not bound to system:playback
                    #     This alows you to send audio to other jack ports, for example
                    #     to send it to a remote loudspeaker.

                    # On this example the sound card has 2 playback ports (1 & 2)
                    # used for the Left active loudspeaker LO & HI.
                    # CamillaDSP (cpal 3 & 4) will be used to send to a remote Right loudspeaker pair

                    #num    name    Gain dB    Polarity     Delay       bind to
                    #                          +/-          ms
                    1:      lo.L    0.0         +           0.0
                    2:      hi.L    0.0         +           0.0
                    3:      lo.R    0.0         +           0.0         remote_lo
                    4:      hi.R    0.0         +           0.0         remote_hi

                Here will convert the Human Readable fields into a dictionary.
            """

            def check_LR_pairs():

                n_L = 0
                n_R = 0

                for out, params in LSPK_CONFIG["outputs"].items():

                    name = params.get('name', '')

                    if not name:
                        continue

                    if name.endswith('.L'):
                        n_L += 1

                    elif name.endswith('.R'):
                        n_R += 1

                    elif name == 'sw':
                        pass

                    else:
                        raise Exception(f"(lspk.yml) ERROR bad output name {name}")

                if n_L != n_R:
                    raise Exception(f'(lspk.yml) ERROR number of outputs for L and R does not match')


            def make_simple_LR_outputs_map():

                LSPK_CONFIG["outputs"] = {
                    0: {
                        "name":         'fr.L',
                        "gain":         0.0,
                        "polarity":     "+",
                        "delay":        0.0,
                        "bindto":       ''
                    },
                    1: {
                        "name":         'fr.R',
                        "gain":         0.0,
                        "polarity":     "+",
                        "delay":        0.0,
                        "bindto":       ''
                    }
                }


            def check_order():
                """ The output numbers must be ordered and consecutive """
                outs_list = list( LSPK_CONFIG["outputs"].keys() )
                return outs_list == list(range(1, len(outs_list) + 1))


            def get_fields(out, tmp):

                # only name is mandatory
                tmp = tmp.split() + ['', '', '','']

                name, gain, polarity, delay, bindto = tmp[:5]

                if gain != '':
                    gain = float(gain)
                else:
                    gain = 0.0

                if not polarity:
                    polarity = '+'
                else:
                    if not polarity in ('+', '-'):
                        raise Exception(f"(lspk.yml) ERROR in output {out}, polarity must be '+' or '-'")

                if delay != '':
                    delay = float(delay)
                else:
                    delay = 0.0

                if bindto and 'system' in bindto:
                    raise Exception(f"(lspk.yml) ERROR in output {out}, bindport cannot be 'system:...'")

                return  name, gain, polarity, delay, bindto


            # Default simple stereo full range outputs
            if not LSPK_CONFIG.get('outputs'):
                make_simple_LR_outputs_map()
                return

            if not check_order():
                raise Exception('(lspk.yml) ERROR outputs numbers map must be complete')


            for out, params_str in LSPK_CONFIG["outputs"].items():

                if params_str:

                    # It is expected to found 5 fields in the params string
                    name, gain, polarity, delay, bindto = get_fields(out, params_str)

                    LSPK_CONFIG["outputs"][out] = {
                        'name':         name,
                        'gain':         gain,
                        'polarity':     polarity,
                        'delay':        delay,
                        'bindto':       bindto
                    }

                else:
                    LSPK_CONFIG["outputs"][out] = {
                        'name':         '',
                        'gain':         None,
                        'polarity':     None,
                        'delay':        None,
                        'bindto':       ''
                    }

            # Check L/R pairs
            check_LR_pairs()


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

    CONFIG["application"] = 'pAudio'

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
    CONFIG['paudio_addr']     = CONFIG.get('paudio_addr',     '0.0.0.0')
    CONFIG['paudio_port']     = CONFIG.get('paudio_port',     9990)
    CONFIG['camilladsp_port'] = CONFIG.get('camilladsp_port', 1234)

    # CamillaDSP activation wait (default 0.1 s)
    # If you experience problems with CamillaDSP on JACK in slow machines, like
    #     BDB2034 unable to allocate memory for mutex; resize mutex region
    # then slightly increase this value under config.yml.
    CONFIG['camilladsp_activation_wait'] = CONFIG.get('camilladsp_activation_wait', 0.1)


    if "jack" in CONFIG:
        complete_jack_params()

    elif 'coreaudio' in CONFIG:
        # We need to prepare Coreaudio capture section
        prepare_coreaudio_init_devices()


    if not "samplerate" in CONFIG:
        CONFIG["samplerate"] = 44100
        print(f'{Fmt.BOLD}\n(config) !!! samplerate NOT configured, default to fs=44100\n{Fmt.END}')

    if not CONFIG.get("plugins"):
        CONFIG["plugins"] = []

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

    # 2. Loudspeaker EQ:
    CONFIG["lspk_eq"] = {}

    if lspk_config.get('lspk_eq'):
        CONFIG["lspk_eq"] = lspk_config["lspk_eq"]

    CONFIG["lspk_eq_posit_gain"] = lspk_config.get('lspk_eq_posit_gain', 0.0)

    # 3. Loudspeaker DRC:
    CONFIG["drc"] = {}

    if lspk_config.get('drc'):
        CONFIG["drc"] = lspk_config["drc"]

    write_pAudio_cfg(CONFIG)


if pAudio_cfg_is_recent():
    print(f'{Fmt.GRAY}(config) loading pAudio_cfg from disk.{Fmt.END}')
    try:
        CONFIG = read_pAudio_cfg()
    except Exception as e:
        print(f'{Fmt.RED}{Fmt.BLINK}(config) PANIC reading: {PAUDIO_CFG_PATH}: {str(e)}{Fmt.END}')
        sys.exit()

    LOUDSPEAKER   = CONFIG.get('loudspeaker', '')
    LSPKFOLDER    = f'{LSPKSFOLDER}/{LOUDSPEAKER}'

else:
    print(f'{Fmt.BLUE}(config) preparing pAudio_cfg ...{Fmt.END}')
    complete_config()

