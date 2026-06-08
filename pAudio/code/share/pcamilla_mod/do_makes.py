#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import subprocess as sp
import os

UHOME = os.path.expanduser('~')

CAMILLADSP_VERSION = 3
try:
    tmp = sp.check_output(f'{UHOME}/bin/camilladsp --version', shell=True).decode().lower()
    if 'camilladsp' in tmp:
        tmp = tmp.split()[1][0]
        if tmp.isdigit():
            CAMILLADSP_VERSION = int(tmp)

except Exception as e:
    print(f'(do_makes) error getting the CamillaDSP version: {str(e)}')


def make_gain_filter(gain, description=''):
    res =   {
                'description': description,
                'type': 'Gain',
                'parameters': {
                        'gain':     gain,
                        'inverted': False,
                        'mute':     False
                }
            }
    return res


def make_dither_filter(d_type, bits):
    f= {
        'type': 'Dither',
        'parameters': {
            'type': d_type,
            'bits': bits
        }
    }
    return f


def make_fir_filter(fir_path):

    fmt = 'FLOAT32LE'
    if CAMILLADSP_VERSION >= 4:
       fmt = 'F32_LE'

    f = {
            "type": 'Conv',
            "parameters": {
                "filename": fir_path,
                "format":   fmt,
                "type":     'Raw'
            }
        }

    return f


def make_xo_iir_filter(way_type='hi', subtype='LR', order=2, freq=2000, freq2=0):
    """
        way_type:   lo | hi | mi *
        subtype:    LinkwitzRiley | Butterworth
        freq:       (Hz)
        order:      (even if LinkwitzRiley)

        (*) Bandpass (mi) is PENDING
    """

    subtype = subtype.lower()

    if 'lr' in subtype or 'linkw' in subtype:
        subtype = 'LinkwitzRiley'

        # check order is even for LR
        if order % 2:
            raise Exception('LinkwitzRiley order MUST be even')

    elif 'but' in subtype:
        subtype = 'Butterworth'

    if way_type == 'hi':
        subtype += 'Highpass'

    elif way_type == 'lo':
        subtype += 'Lowpass'

    f = {   'type':         'BiquadCombo',
            'parameters': {
                'type':     subtype,
                'order':    order,
                'freq':     freq
            }
        }

    return f


def make_delay_filter(delay=0.0, description=''):

    f = {
            "description": description,
            "type": 'Delay',
            "parameters": {
                "delay":     delay,
                "unit":      'ms',
                "subsample": False
            }
        }

    return f


def make_mixer_preamp(midside_mode='normal', swap_LR=False):
    r"""
        modes:

            normal
            mid     (mono)
            side    (L - R)
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
            g01 =  0.0; i01 = False; m01 = True;     g11 =  0.0; i11 = True;  m11 = False

        case 'solo_L':
            g00 =  0.0; i00 = False; m00 = False;    g10 =  0.0; i10 = False; m10 = True
            g01 =  0.0; i01 = False; m01 = True;     g11 =  0.0; i11 = False; m11 = True

        case 'solo_R':
            g00 =  0.0; i00 = False; m00 = True;     g10 =  0.0; i10 = False; m10 = True
            g01 =  0.0; i01 = False; m01 = True;     g11 =  0.0; i11 = False; m11 = False


    match swap_LR:

        case False:
            src_0 = 0
            src_1 = 1

        case True:
            src_0 = 1
            src_1 = 0

        case _:
            raise ValueError('make_mixer_preamp swap_LR must be boolean')


    m = {
        'channels': { 'in': 2, 'out': 2 },
        'mapping': [
            {   'dest': 0,
                'sources': [
                    {'channel': src_0, 'gain': g00, 'inverted': i00, 'mute': m00},
                    {'channel': src_1, 'gain': g10, 'inverted': i10, 'mute': m10},
                ]
            },
            {   'dest': 1,
                'sources': [
                    {'channel': src_0, 'gain': g01, 'inverted': i01, 'mute': m01},
                    {'channel': src_1, 'gain': g11, 'inverted': i11, 'mute': m11},
                ]
            }
        ]
    }

    m["description"] = f'midside-{midside_mode}'
    if swap_LR:
        m["description"] += ' (R <> L swapped)'


    return m


def make_expand_mixer(pAudio_outputs):
    """ Makes a mixer to route L/R to several outputs

        Example of a weird 2+1 way

        out     way
        ---     ---
        0       sw
        1
        2       lo.L
        3       lo.R
        4       hi.L
        5       hi.R


          from2to5channels:
            channels:
              in: 2
              out: 4
            mapping:
            - dest: 0
              sources:
              - channel: 0
                gain: -3.0
                inverted: false
              - channel: 1
                gain: -3.0
                inverted: false
            - dest: 2
              sources:
              - channel: 0
                gain: 0.0
                inverted: false
            - dest: 3
              sources:
              - channel: 1
                gain: 0.0
                inverted: false
            - dest: 4
              sources:
              - channel: 0
                gain: 0.0
                inverted: false
            - dest: 5
              sources:
              - channel: 1
                gain: 0.0
                inverted: false
    """

    def audio_ch_to_cam_ch(ch):
        return {'L': 0, 'R': 1}[ch.split('.')[-1]]


    def pol2inv(pol):
        return { '+':  False,
                 '-':  True,
                 '1':  False,
                '-1':  True,
                   1:  False,
                  -1:  True
              }[pol]


    description = f'Outputs map: '
    mapping     = []

    for out, params in pAudio_outputs.items():

        dest = int(out) - 1 # because the configuration could be processed using json
        name = params["name"]

        if name.endswith('.L') or name.endswith('.R'):

            # L / R  --->  0 / 1
            src_ch = audio_ch_to_cam_ch( params['name'] )

            mapping.append( {   'dest': dest,
                                'sources': [ {  'channel':   src_ch,
                                                'gain':      params["gain"],
                                                'inverted':  pol2inv(params["polarity"])
                                      } ]
                        } )

        elif 'sw' in name.lower():

            mapping.append( {   'dest': dest,
                                'sources': [ {  'channel':   0,
                                                'gain':      params["gain"] / 2.0 - 3.0,
                                                'inverted':  pol2inv(params["polarity"])
                                             },
                                             {  'channel':   1,
                                                'gain':      params["gain"] / 2.0 - 3.0,
                                                'inverted':  pol2inv(params["polarity"])
                                             }
                                           ]
                        } )


        description += f"{name if name else '-' }/{out}, "

    # remove tail
    description = description.strip()[:-1]


    m = {   'description':  description,
            'channels':     { 'in': 2, 'out': len(pAudio_outputs) },
            'mapping':      mapping
        }

    return m


def make_xover_steps(pAudio_outputs, xo_filtername):
    """ Makes the Filter steps after the expander mixer of the pipeline

            Example of a weird 2+1 way

            out     way
            ---     ---
            0       sw
            1
            2       lo.L
            3       lo.R
            4       hi.L
            5       hi.R


          - type: Filter
            channel: 0
            names:
              - sw
              - sw_gain
              - delay.sw

          - type: Filter
            channel: 2
            names:
              - lo.mp
              - lo.mp_gain
              - delay.lo.L

          - type: Filter
            channel: 3
            names:
              - lo.mp
              - lo.mp_gain
              - delay.lo.R

          - type: Filter
            channel: 4
            names:
              - hi.mp
              - hi.mp_gain
              - delay.hi.L

          - type: Filter
            channel: 5
            names:
              - hi.mp
              - hi.mp_gain
              - delay.hi.R

    """


    def audio_ch_to_cam_ch(ch):
        return {'L': 0, 'R': 1}[ch]

    steps = []

    for out, params in pAudio_outputs.items():

        dest = int(out) - 1 # because the configuration could be processed using json
        name = params["name"]

        if not name:
            continue

        if not 'sw' in name.lower():
            # lo.R --> lo
            way = name.replace('.L', '').replace('.R', '')
        else:
            way = name


        step = {    'description':  f'xover.{name}',

                    'type':         'Filter',

                    # must be a list
                    'channels':     [dest],

                    'names':        [ f'xo.{way}.{xo_filtername}',
                                      f'xo.{way}.{xo_filtername}_gain',
                                      f'delay.{name}'
                                    ]
                }

        steps.append( step )

    return steps


def make_peq_filter(freq=1000, gain=-3.0, qorbw=1.0, mode='q'):
    """
    type: Biquad
    parameters:
      type: Peaking
      freq: 100
      gain: -7.3
      q: 0.5       /   bandwidth: 0.7
    """

    f = {   'type':         'Biquad',
            'parameters': {
                'type':     'Peaking',
                'freq':     freq,
                'gain':     gain
            }
        }

    if mode == 'q':
        f["parameters"]["q"] = qorbw
    elif mode == 'bw':
        f["parameters"]["bw"] = qorbw
    else:
        raise Exception(f'Bad PEQ filter mode `{mode}` must be `q` or `bw`')

    return f

