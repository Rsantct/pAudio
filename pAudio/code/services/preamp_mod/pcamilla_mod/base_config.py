#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

from .do_makes import *

Fmt      = None
EQFOLDER = ''


def prepare_base_config(pAudio_config, cam_config):

    def prepare_devices():

        chunksize = 1024

        # Coreaudio
        if pAudio_config.get('coreaudio'):

            cam_config["devices"] = pAudio_config["coreaudio"].get('devices')

            cam_config["devices"]["capture"] ["type"] = 'CoreAudio'
            cam_config["devices"]["playback"]["type"] = 'CoreAudio'


        # Jack
        elif pAudio_config.get('jack'):

            out_channels = 2

            if pAudio_config.get('outputs'):
                out_channels = len( pAudio_config.get('outputs') )

            if pAudio_config["jack"].get('period'):
                chunksize = pAudio_config["jack"].get('period')

            cam_config["devices"] = {

                'capture': {    'channels':     2,
                                'device':       'default',
                                'type':         'Jack'
                            },

                'playback': {   'channels':     out_channels,
                                'device':       'default',
                                'type':         'Jack'
                            }
            }

        else:
            print(f'{Fmt.BOLD}Audio backend still not supported{Fmt.END}')
            sys.exit()


        cam_config["devices"]["samplerate"]         = pAudio_config["samplerate"]

        cam_config["devices"]["chunksize"]          = chunksize

        cam_config["devices"]["silence_threshold"]  = -80

        cam_config["devices"]["silence_timeout"]    = 30


    def prepare_filters():

        cam_config["filters"] =    {

        # Balance and Polarity
        'bal_pol_L':            make_gain_filter(0.0, 'Balance and Polarity Left'),
        'bal_pol_R':            make_gain_filter(0.0, 'Balance and Polarity Right'),

        # Dither
        'dither':               make_dither_filter('Shibata441', 16),

        # lspk EQ safe gain
        'lspk_eq_safe_gain':    make_gain_filter(0.0, 'gain compensation for lspk EQ'),

        # lspk DRC gain offset
        'drc_gain_offset':      make_gain_filter(0.0, 'gain offset for DRC in use (only for DRC-FIR)'),

        # LU OFFSET
        'lu_offset':            make_gain_filter(0.0, 'LU OFFSET (compensation for Loudness War)'),

        # Preamp EQ (tones anf loudnes curves)
        'preamp_eq':            make_fir_filter( f'{EQFOLDER}/eq_flat.pcm' )
        }


    def prepare_mixers():
        """ Only preamp mixer at init
        """

        cam_config["mixers"] = {}

        cam_config["mixers"]["preamp_mixer"] = make_mixer_preamp()


    def prepare_pipeline():

        cam_config["pipeline"] = [

            # Input stereo preamp mixer
            {   'type': 'Mixer', 'name': 'preamp_mixer'
            },

            # Stereo filtering at preamp stage
            {   'description':  'preamp.L',
                'channels':     [0],
                'type':         'Filter',
                'names':        ['preamp_eq', 'lspk_eq_safe_gain', 'drc_gain_offset', 'lu_offset', 'bal_pol_L']
            },
            {   'description':  'preamp.R',
                'channels':     [1],
                'type':         'Filter',
                'names':        ['preamp_eq', 'lspk_eq_safe_gain', 'drc_gain_offset', 'lu_offset', 'bal_pol_R']
            }
        ]


    prepare_devices()
    prepare_filters()
    prepare_mixers()
    prepare_pipeline()


def append_dither(pAudio_config, cam_config):
    """ Adjust the dither filter as per the output sample format and samplerate
    """

    def get_bit_depth(fmt):
        """ retrieves the bit depth from a given audio sample format,
            e.g. FLOAT32LE, S24LE, ...
        """
        digits = [x for x in fmt if x.isdigit()]
        bd = ''.join(digits)
        return int(bd)


    if not( pAudio_config.get("coreaudio") and pAudio_config["coreaudio"]["devices"]["playback"].get("dither") ):
        return

    # First of all we need to remove the pAudio dither parameter.
    # It was included in pAudio playback device because logical order,
    # but it is not a CamillaDSP devices parameter.
    del cam_config["devices"]["playback"]["dither"]

    # Update `dither` filter parameters

    dither_bits = get_bit_depth( cam_config["devices"]["playback"]["format"] )

    # https://github.com/HEnquist/camilladsp#dither
    match cam_config["devices"]["samplerate"]:
        case 44100:     d_type = 'Shibata441'
        case 48000:     d_type = 'Shibata48'
        case _:         d_type = 'Simple'

    cam_config["filters"]["dither"] = make_dither_filter(d_type, dither_bits)

    # Add dither to the last steps of the pipeline

    step_type = ''
    last_step_type = ''

    for step in cam_config["pipeline"][::-1]:

        if step.get('description'):

            # Multiway have XOVER in last steps of the pipeline
            if 'xover.' in step.get('description').lower():
                step_type = 'xover'

            # Full Range can have PREAMP, and optionally EQ and/or DRC
            else:

                if   '(drc'    in step.get('description').lower():
                    step_type = 'drc'
                elif '(eq'     in step.get('description').lower():
                    step_type = 'eq'
                elif 'preamp.' in step.get('description').lower():
                    step_type = 'preamp'

            if last_step_type and step_type != last_step_type:
                break

            if step_type in ('xover', 'drc', 'eq', 'preamp'):
                step["names"].append('dither')

            last_step_type = step_type
