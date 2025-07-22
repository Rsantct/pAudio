#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.


def make_dither_filter(d_type, bits):
    f= {
        'type': 'Dither',
        'parameters': {
            'type': d_type,
            'bits': bits
        }
    }
    return f


def make_drc_filter(channel, drc_set, fs, lspkfolder):

    fir_path = f'{lspkfolder}/{fs}/drc.{channel}.{drc_set}.pcm'

    f = {
            "type": 'Conv',
            "parameters": {
                "filename": fir_path,
                "format":   'FLOAT32LE',
                "type":     'Raw'
            }
        }

    return f


def make_xo_filter(xo_filter, fs, lspkfolder):

    fir_path = f'{lspkfolder}/{fs}/xo.{xo_filter}.pcm'

    f = {
            "type": 'Conv',
            "parameters": {
                "filename": fir_path,
                "format":   'FLOAT32LE',
                "type":     'Raw'
            }
        }

    return f


def make_delay_filter(delay):

    f = {
            "type": 'Delay',
            "parameters": {
                "delay":     delay,
                "unit":      'ms',
                "subsample": False
            }
        }

    return f


def make_mixer_preamp(midside_mode='normal'):
    r"""
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
            g01 =  0.0; i01 = False; m01 = True;     g11 =  0.0; i11 = True;  m11 = False

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


def make_mixer_multi_way(pAudio_outputs):
    """ Makes a mixer to route L/R to multiway outputs

        --> and returns the number of used outputs

        Example for 2+1 way, with 'sw' way connected to the 6th output

          from2to5channels:
            channels:
              in: 2
              out: 4
            mapping:
            - dest: 0
              sources:
              - channel: 0
                gain: 0.0
                inverted: false
            - dest: 1
              sources:
              - channel: 1
                gain: 0.0
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
            - dest: 5
              sources:
              - channel: 0
                gain: -3.0
                inverted: false
              - channel: 1
                gain: -3.0
                inverted: false
    """

    def ch2num(ch):
        return {'L': 0, 'R': 1}[ch]


    def pol2inv(pol):
        return { '+':  False,
                 '-':  True,
                 '1':  False,
                '-1':  True,
                   1:  False,
                  -1:  True
              }[pol]


    mapping     = []
    description = f'Sound card map: '

    for dest, params in pAudio_outputs.items():

        way = params["name"]

        if way.endswith('.L') or way.endswith('.R'):

            mapping.append( {   'dest': dest - 1,
                                'sources': [ {  'channel':   ch2num(way[-1]),
                                                'gain':      params["gain"],
                                                'inverted':  pol2inv(params["polarity"])
                                      } ]
                        } )

        elif 'sw' in way.lower():

            mapping.append( {   'dest': dest - 1,
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

        description += f'{dest}/{way}, '


    # remove tail
    description = description.strip()[:-1]

    m = {   'description':  description,
            'channels':     { 'in': 2, 'out': len( pAudio_outputs ) },
            'mapping':      mapping,
        }

    return m


def make_xover_steps(pAudio_outputs, default_filter_type = 'mp'):
    """ Makes the Filter steps after the expander mixer of the pipeline

        Example for 2+1 way, with 'sw' way connected to the 6th output

          - type: Filter
            channel: 0
            names:
              - lo.mp
              - delay.lo.L

          - type: Filter
            channel: 1
            names:
              - lo.mp
              - delay.lo.R

          - type: Filter
            channel: 2
            names:
              - hi.mp
              - delay.hi.L

          - type: Filter
            channel: 3
            names:
              - hi.mp
              - delay.hi.R

          - type: Filter
            channel: 5
            names:
              - sw
              - delay.sw
    """

    steps = []

    for out_idx, out_params in pAudio_outputs.items():

        if not out_params["name"]:
            continue

        if not 'sw' in out_params["name"]:
            # lo.R --> lo
            way = out_params["name"].replace('.L', '').replace('.R', '')
        else:
            way = 'sw'

        ch = out_params["name"].split('.')[-1]

        step = {    'description':  f'xover.{way}.{ch}',

                    'type':         'Filter',

                                    # output indexes starts with `1` like
                                    # jack `system:playback_N` ports numbering
                    'channels':     [out_idx - 1],

                    'names':        [ f'xo.{way}.{default_filter_type}',
                                      f'delay.{way}.{ch}'
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

