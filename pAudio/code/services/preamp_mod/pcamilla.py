#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  os
import  sys
import  shutil
import  subprocess as sp
from    time import sleep
import  yaml
import  json
from    camilladsp import CamillaClient
import  jack
import  make_eq as mkeq

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from    common import *

#####
# (!) use set_config_sync(some_config) to upload a new one
#####


# The CamillaDSP connection
HOST        = '127.0.0.1'
PORT        = 1234
PC = CamillaClient(HOST, PORT)


def _connect_to_camilla():

    tries = 15   # 3 sec

    while tries:
        try:
            PC.connect()
            break
        except:
            sleep(.2)
            tries -= 1

    if not tries:
        print(f'{Fmt.RED}Unable to connect to CamillaDSP, check log folder.{Fmt.END}')
        return False

    return True


def _init():
    """ CamillaDSP needs a new FIR filename in order to
        reload the convolver coeffs
    """
    global LAST_EQ, EQ_LINK

    EQ_LINK = f'{EQFOLDER}/eq.pcm'

    LAST_EQ = 'A'

    shutil.copy(f'{EQFOLDER}/eq_flat.pcm', f'{EQFOLDER}/eq_A.pcm')
    shutil.copy(f'{EQFOLDER}/eq_flat.pcm', f'{EQFOLDER}/eq_B.pcm')


def set_config_sync(cfg, wait=0.1):
    """ (i) When ordering set config some time is needed to be running
        This is a fake sync, but just works  >:-)
    """
    PC.config.set_active(cfg)
    sleep(wait)


def get_state():
    """ This is the internal camillaDSP state """
    return PC.general.state()


def get_config():
    return PC.config.active()


def print_pipeline(cfg):
    print('-'*80)
    for s in cfg["pipeline"]:
        print(s)
    print()


def _prepare_cam_config(pAudio_config):
    """ Updates camilladsp config as per the user pAudio configuration
    """

    def prepare_base_config():

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
            'bal_pol_L':    {  'type': 'Gain',
                                'parameters': {
                                    'gain':     0.0,
                                    'inverted': False,
                                    'mute':     False
                                }
                            },
            'bal_pol_R':    {  'type': 'Gain',
                                'parameters': {
                                    'gain':     0.0,
                                    'inverted': False,
                                    'mute':     False
                                }
                            },

            # Dither
            'dither':   {   'type': 'Dither',
                            'parameters': {'bits': 16, 'type': 'Shibata441'},
                        },

            # DRC gain
            'drc_gain': {   'type': 'Gain',
                            'parameters': {
                                    'gain':     0.0,
                                    'inverted': False,
                                    'mute':     False
                            }
                        },

            # LU OFFSET (compensation for Loudness War)
            'lu_offset': {  'type': 'Gain',
                            'parameters': {
                                    'gain':      0.0,
                                    'inverted': False,
                                    'mute':     False
                            }
                        },

            # Preamp EQ (tones anf loudnes curves)
            'preamp_eq':    {   'type': 'Conv',
                                'parameters': {
                                    'filename': f'{EQFOLDER}/eq_flat.pcm',
                                    'format': 'FLOAT32LE',
                                    'type': 'Raw'
                                }
                        }
            }


        def prepare_mixers():
            """ Only preamp mixer at init
            """

            cam_config["mixers"] = {}

            cam_config["mixers"]["preamp_mixer"] = make_preamp_mixer()


        def prepare_pipeline():

            cam_config["pipeline"] = [

                # Input stereo preamp mixer
                {   'type': 'Mixer', 'name': 'preamp_mixer'
                },

                # Stereo filtering at preamp stage
                {   'description':  'preamp.L',
                    'channels':     [0],
                    'type':         'Filter',
                    'names':        ['preamp_eq', 'drc_gain', 'lu_offset', 'bal_pol_L']
                },
                {   'description':  'preamp.R',
                    'channels':     [1],
                    'type':         'Filter',
                    'names':        ['preamp_eq', 'drc_gain', 'lu_offset', 'bal_pol_R']
                }
            ]


        prepare_devices()
        prepare_filters()
        prepare_mixers()
        prepare_pipeline()


    def prepare_multiway_structure():
        """ The multiway N channel expander Mixer
        """

        def update_xo_stuff():
            """ This is the LAST step into the PIPELINE.
            """

            xo_filters = get_xo_filters_from_loudspeaker_folder()

            if xo_filters:
                print(f'{Fmt.BLUE}{Fmt.BOLD}Found loudspeaker XOVER filter PCMs: {xo_filters}{Fmt.END}')

            else:
                print(f'{Fmt.BOLD}{Fmt.BLINK}Loudspeaker xover PCMs NOT found{Fmt.END}')


            # xo filters
            for xo_filter in (xo_filters):
                cam_config["filters"][f'xo.{xo_filter}'] = make_xo_filter(xo_filter, pAudio_config["samplerate"])

            # Auxiliary delay filters definition
            for _, pms in CONFIG["outputs"].items():
                if not pms["name"]:
                    continue
                cam_config["filters"][f'delay.{pms["name"]}'] = make_delay_filter(pms["delay"])

            # pipeline
            if xo_filters:
                make_xover_steps(cam_config)


        # Prepare the needed expander mixer
        mixer_name = make_multi_way_mixer(cam_config)
        #
        # and adding it to the pipeline
        mwm = {'type': 'Mixer', 'name': mixer_name}
        cam_config["pipeline"].append(mwm)

        # The final step in the pipeline: XO
        update_xo_stuff()


    def update_dither():
        """ Adjust the dither filter as per the output sample format and samplerate
        """

        if not( pAudio_config.get("coreaudio") and pAudio_config["coreaudio"]["devices"]["playback"].get("dither") ):
            return

        # First we need to remove dither parameter.
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

                if 'preamp.' in step.get('description'):
                    step_type = 'preamp'

                elif 'xover.' in step.get('description'):
                    step_type = 'xover'

                if step_type in ('preamp', 'xover'):
                    step["names"].append('dither')

                last_step_type = step_type

                if step_type and step_type != last_step_type:
                    break


    def update_drc_stuff():

        # drc filters
        for drcset in pAudio_config["drc_sets"]:
            for ch in 'L', 'R':
                cam_config["filters"][f'drc.{ch}.{drcset}'] = make_drc_filter(ch, drcset, pAudio_config["samplerate"])

        # The initial pipeline points to the FIRST drc_set
        insert_drc_to_pipeline(cam_config, drcID=pAudio_config["drc_sets"][0])


    def update_peq_stuff():

        # Filters section
        for ch in CONFIG["PEQ"]:
            for peq, pms in CONFIG["PEQ"][ch].items():
                cam_config["filters"][f'peak.{ch}.{peq}'] = \
                    make_peq_filter(pms["freq"], pms["gain"], pms["q"])

        # Pipeline
        npL = 0
        npR = 0
        for p in [x for x in cam_config["filters"] if x.startswith('peak.')]:
            if '.L' in p:
                cam_config["pipeline"][1]["names"].append(p)
                npL += 1
            elif '.R' in p:
                cam_config["pipeline"][2]["names"].append(p)
                npR += 1

        # Filling with dummies to balance number of peaking in L and R
        if npL != npR:
            cam_config["filters"][f'peak.dummy'] = \
                make_peq_filter(freq=20, gain=0.0, qorbw=1.0)
        if npL < npR:
            for i in range(npR - npL):
                cam_config["pipeline"][1]["names"].append('peak.dummy')
        if npR < npL:
            for i in range(npL - npR):
                cam_config["pipeline"][2]["names"].append('peak.dummy')


    # From here `cam_config` will grow progressively
    cam_config = {}

    # Prepare CamillaDSP base config
    prepare_base_config()

    # The PEQ **PENDING TO REVIEW**
    # update_peq_stuff()

    # FIR DRCs **PENDING TO REVIEW**
    #if pAudio_config["drc_sets"]:
    #    update_drc_stuff()

    # Multiway if more than 2 outputs
    outputs_in_use = [ x for x in CONFIG["outputs"] if CONFIG["outputs"][x].get('name') ]
    if len(outputs_in_use) > 2:
        prepare_multiway_structure()

    # Dither
    update_dither()

    # Dumping config
    with open(f'{LOGFOLDER}/camilladsp_init.yml', 'w') as f:
        yaml.safe_dump(cam_config, f)

    return cam_config


def init_camilladsp(pAudio_config):
    """ Updates camilladsp.yml with user configs,
        includes auto making the DRC yaml stuff,
        then runs the CamillaDSP process.

        returns a <string>:

            'done' OR 'some problem description...'
    """

    def cpal_ports_ok(cpal2system_alowed=True):
        """ Check for:

            - no weird cpal ports named like `cpal_client_in-01`

            - no cpal ports are connected to system ports (optional)

            (bool)
        """

        result = True

        jcli = jack.Client(name='tmp', no_start_server=True)

        cpal_ports = jcli.get_ports('cpal_client')

        for cpal_port in cpal_ports:

            # Early return if any `cpal_client_in-01` is detected
            if '-' in cpal_port.name:
                print(f'{Fmt.BOLD}Weird CamillaDSP behavior having port: {cpal_port.name}{Fmt.END}')
                result = False
                break

            if cpal2system_alowed:
                continue

            conns = jcli.get_all_connections( cpal_port )

            for c in conns:
                if 'system' in c.name:
                    print(f'{Fmt.BOLD}CPAL <--> SYSTEM detected: {cpal_port.name} {c.name}{Fmt.END}')
                    result = False

        jcli.close()

        return result


    def check_cdsp_running(timeout=10):

        def grep_log_errors():
            with open(f'{LOGFOLDER}/camilladsp.log', 'r') as f:
                logs = f.read().strip().split('\n')
            return [l.strip() for l in logs if 'ERROR' in l]


        period = .5
        tries = int(timeout / period)

        while tries:

            s = PC.general.state()
            if str(s) == 'ProcessingState.RUNNING':
                break
            else:
                print(f'{Fmt.BLUE}{"." * int(tries * period)}{Fmt.END}')

            sleep(.5)
            tries -= 1

        if tries:
            return True
        else:
            for x in grep_log_errors():
                print(f'{Fmt.RED}{x}{Fmt.END}')
            return False


    global PC

    # Prepare the camilladsp.yml as per the pAudio user configuration
    cfg_init = _prepare_cam_config(pAudio_config)

    # Stop if any process running
    sp.call('pkill -KILL camilladsp'.split())

    # Starting CamillaDSP (MUTED)
    print(f'{Fmt.BLUE}Logging CamillaDSP to log/camilladsp.log ...{Fmt.END}')
    cdsp_cmd = f'camilladsp --wait -m -a 127.0.0.1 -p 1234 ' + \
               f'--logfile "{LOGFOLDER}/camilladsp.log"'
    p = sp.Popen( cdsp_cmd, shell=True )
    sleep(1)


    if _connect_to_camilla():
        print(f'{Fmt.BLUE}Connected to CamillaDSP websocket.{Fmt.END}')

    else:
        print(f'{Fmt.BOLD}ERROR connecting to CamillaDSP websocket.{Fmt.END}')
        return str(e)


    # Loading configuration
    try:
        print(f'Trying to load configuration and run.')
        PC.config.set_active(cfg_init)

        if check_cdsp_running(timeout=5):

            # Check CPAL jack ports
            if not cpal_ports_ok():
                return f'problems with Camilla DSP CPAL ports'

            # ALL IS OK
            return 'done'

        else:
            return f'Cannot start `camilladsp` process, see `pAudio/log`'

    except Exception as e:

        print(f'{Fmt.BOLD}ERROR loading CamillaDSP configuration. {str(e)}{Fmt.END}')
        return str(e)


def clear_filters(cfg, pattern=''):
    if pattern:
        keys = []
        for f in cfg["filters"]:
            if f.startswith(pattern):
                keys.append(f)
        for k in keys:
            del cfg["filters"][k]


def clear_mixers(cfg, pattern=''):
    if pattern:
        keys = []
        for m in cfg["mixers"]:
            if m.startswith(pattern):
                keys.append(m)
        for k in keys:
            del cfg["mixers"][k]


def clear_pipeline_input_filters(cfg, pattern=''):
    """ Clears elements inside the 2 first filters of the pipeline.
        That is, the pipeline steps 1 and 2
    """
    if pattern:
        for n in (1, 2):
            names_old = cfg["pipeline"][n]['names']
            names_new = list_remove_by_pattern(names_old, pattern)
            cfg["pipeline"][n]['names'] = names_new


def clear_pipeline_output_filtering(cfg):
    """ Remove output xo Filter steps from pipeline
    """
    p_old = cfg["pipeline"]
    p_new = []

    for step in p_old:
        if step["type"] != 'Filter':
            p_new.append(step)
        else:
            names = step["names"]
            if not [n for n in names if 'xo' in n]:
                p_new.append(step)

    cfg["pipeline"] = p_new


def clear_pipeline_mixer(cfg, pattern=''):
    """ Clears mixer steps from the pipeline
    """
    def remove_mixer(l, p):
        l = [ x for x in l
                if (x["type"]=='Mixer' and p not in x["name"])
                   or
                   x["type"]!='Mixer'
            ]
        return l

    if pattern:
        steps_old = cfg["pipeline"]
        steps_new = remove_mixer(steps_old, pattern)
        cfg["pipeline"] = steps_new


def insert_drc_to_pipeline(cfg, drcID = ''):
    for n in (1,2):
        names_old = cfg["pipeline"][n]['names']
        names_new = list_remove_by_pattern(names_old, 'drc.')
        names_new.insert(1, f'drc.L.{drcID}')
        cfg["pipeline"][n]['names'] = names_new


def append_item_to_pipeline(cfg, item = ''):
    for n in (1,2):
        names_old = cfg["pipeline"][n]['names']
        names_new = list_remove_by_pattern(names_old, item)
        names_new.append(item)
        cfg["pipeline"][n]['names'] = names_new


def reload_eq():

    def toggle_last_eq():
        global LAST_EQ
        LAST_EQ = {'A':'B', 'B':'A'}[LAST_EQ]


    mkeq.make_eq()
    eq_path  = f'{EQFOLDER}/eq_{LAST_EQ}.pcm'
    mkeq.save_eq_IR(eq_path)

    # For convenience, it will be symlinked to eq.pcm,
    # so that a viewer could display the current curve
    if os.path.isfile(EQ_LINK) or os.path.islink(EQ_LINK):
        os.unlink(EQ_LINK)
    os.symlink(eq_path, EQ_LINK)


    cfg = PC.config.active()
    cfg["filters"]["preamp_eq"]["parameters"]["filename"] = eq_path
    set_config_sync(cfg)

    toggle_last_eq()


def make_dither_filter(d_type, bits):
    f= {
        'type': 'Dither',
        'parameters': {
            'type': d_type,
            'bits': bits
        }
    }
    return f


def make_drc_filter(channel, drc_set, fs):
    fir_path = f'{LSPKFOLDER}/{fs}/drc.{channel}.{drc_set}.pcm'
    f = {
            "type": 'Conv',
            "parameters": {
                "filename": fir_path,
                "format":   'FLOAT32LE',
                "type":     'Raw'
            }
        }
    return f


def make_xo_filter(xo_filter, fs):
    fir_path = f'{LSPKFOLDER}/{fs}/xo.{xo_filter}.pcm'
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


def make_preamp_mixer(midside_mode='normal'):
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


def make_multi_way_mixer(cfg):
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


    tmp         = []
    description = f'Sound card map: '

    number_of_outputs_in_use = 0

    for dest, pms in CONFIG["outputs"].items():

        way = pms["name"]

        if way.endswith('.L') or way.endswith('.R'):
            tmp.append( {'dest': dest - 1,
                         'sources': [ {'channel':   ch2num(way[-1]),
                                       'gain':      pms["gain"],
                                       'inverted':  pol2inv(pms["polarity"])
                                      } ]
                        } )

        elif 'sw' in way.lower():
            tmp.append( {'dest': dest - 1,
                         'sources': [ {'channel':   0,
                                       'gain':      pms["gain"] / 2.0 - 3.0,
                                       'inverted':  pol2inv(pms["polarity"])
                                      },
                                      {'channel':   1,
                                       'gain':      pms["gain"] / 2.0 - 3.0,
                                       'inverted':  pol2inv(pms["polarity"])
                                      } ]
                        } )

        description += f'{dest}/{way}, '

        number_of_outputs_in_use += 1

    description = description.strip()[:-1]

    mixer_name = f'from2to{number_of_outputs_in_use}channels'

    cfg["mixers"][mixer_name] = {
        'channels': { 'in': 2, 'out': len(CONFIG["outputs"]) },
        'mapping': tmp,
        'description': description
    }

    # Useful info
    print(f'{Fmt.GREEN}{mixer_name} | {description}{Fmt.END}')

    return mixer_name


def make_xover_steps(cfg, default_filter_type = 'mp'):
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

    for out_idx, out_params in CONFIG["outputs"].items():

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

        cfg["pipeline"].append(step)


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


# Getting AUDIO

def get_drc_gain():
    return json.dumps( PC.config.active()["filters"]["drc_gain"] )


# Setting AUDIO, allways **MUST** return some string, usually 'done'

def set_mute(mode):

    if mode in (True, 'true', 'on', 1):
        PC.volume.set_main_mute(True)

    if mode in (False, 'false', 'off', 0):
        PC.volume.set_main_mute(False)

    if mode == 'toggle':
        new_mode = {True: False, False: True} [PC.volume.main_mute() ]
        PC.volume.set_main_mute(new_mode)

    return 'done'


def set_midside(mode):

    modes = ('off', 'mid', 'side', 'solo_L', 'solo_R')

    if mode in modes:

        c = PC.config.active()

        if mode == 'off':
            mode = 'normal'

        c["mixers"]["preamp_mixer"] = make_preamp_mixer(midside_mode = mode)
        set_config_sync(c)

        return 'done'

    else:
        return f'mode error must be in: {modes}'


def set_solo(mode):

    c = PC.config.active()

    match mode:
        case 'l' | 'L': m = make_preamp_mixer(midside_mode='solo_L')
        case 'r' | 'R': m = make_preamp_mixer(midside_mode='solo_R')
        case 'off':     m = make_preamp_mixer(midside_mode='normal')
        case _:         return 'solo mode must be in: L | R | off'

    c["mixers"]["preamp_mixer"] = m
    set_config_sync(c)

    return "done"


def set_polarity(mode):
    """ Polarity applied to channels
    """
    if mode in ('normal','off'):    mode = '++'

    modes = ('++', '--', '+-', '-+')

    result = f'Polarity must be in: {modes}'

    c = PC.config.active()

    match mode:

        case '++':      inv_L = False;   inv_R = False
        case '--':      inv_L = True;    inv_R = True
        case '+-':      inv_L = False;   inv_R = True
        case '-+':      inv_L = True;    inv_R = False

    c["filters"]["bal_pol_L"]["parameters"]["inverted"] = inv_L
    c["filters"]["bal_pol_R"]["parameters"]["inverted"] = inv_R

    set_config_sync(c)

    return "done"


def set_volume(dB=None, mode='abs'):
    """ get or set the Main fader volume

        mode: 'add' or 'rel' to make relative changes
    """
    try:

        if 'rel' in mode or 'add' in mode:
            dB = PC.volume.volume(0) + dB

        if dB <= 0:
            PC.volume.set_volume(0, dB)

    except Exception as e:
        pass

    return PC.volume.volume(0)


def set_balance(dB):
    """ negative dBs means towards Left, positive to Right
    """
    c = PC.config.active()
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


def set_xo(xo_set):
    """ xo_set:     mp | lp
    """

    cfg = PC.config.active()

    # Pipeline outputs
    ppln = cfg["pipeline"]

    # Update xo Filter steps
    for step in ppln:
        if step["type"] == 'Filter':
            names = [n for n in step["names"]]
            # The xo filter is located in the 1st position
            if 'xo.' in names[0]:
                if step["names"][0][-3:] in ('.mp', '.lp'):
                    step["names"][0] = step["names"][0].replace('.lp', f'.{xo_set}') \
                                                       .replace('.mp', f'.{xo_set}')

    try:
        set_config_sync(cfg)
        result = 'done'
    except Exception as e:
        result = str(e)

    return result


def set_drc(drcID):

    result = ''

    cfg = PC.config.active()

    if drcID == 'none':
        try:
            clear_pipeline_input_filters(cfg, pattern='drc.')
            set_config_sync(cfg)
            result = 'done'
        except Exception as e:
            result = str(e)

    else:
        try:
            insert_drc_to_pipeline(cfg, drcID)
            set_config_sync(cfg)
            result = 'done'
        except Exception as e:
            result = str(e)

    return result


def set_drc_gain(dB):
    cfg = PC.config.active()
    cfg["filters"]["drc_gain"]["parameters"]["gain"] = dB
    set_config_sync(cfg)
    return 'done'


def set_lu_offset(dB):
    cfg = PC.config.active()
    cfg["filters"]["lu_offset"]["parameters"]["gain"] = dB
    set_config_sync(cfg)
    return 'done'


_init()
