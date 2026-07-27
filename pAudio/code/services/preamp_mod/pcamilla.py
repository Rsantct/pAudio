#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  os
import  sys
import  shutil
import  subprocess      as      sp
import  threading
from    time            import  sleep
import  json
from    camilladsp      import  CamillaClient

import  make_eq         as      mkeq

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from    common import *

from    pcamilla_mod.do_makes       import  *
from    pcamilla_mod.do_clears      import  *
import  pcamilla_mod.lspk           as lspk
import  pcamilla_mod.base_config    as base_config

lspk.Fmt             =  Fmt
base_config.Fmt      =  Fmt
base_config.EQFOLDER =  EQFOLDER


if sys.platform == 'linux' and CONFIG.get('jack'):
    import  jack


# The CamillaDSP client
CC   = CamillaClient('127.0.0.1', CONFIG["camilladsp_port"])


#######################################################33##########
# (!) use ALWAYS THIS FUNCTION to load a new config into CamillaDSP
###################################################################
def set_config_sync(cfg, wait_multiplier=1):
    """ (i) When ordering set config some time is needed to be running
        This is a fake sync, but just works  >:-)
    """

    try:
        CC.config.set_active(cfg)

        # Default wait usually 0.1 is enough for most activations,
        # but when changing the device you need to apply some multiplier
        sleep( CONFIG['camilladsp_activation_wait'] * wait_multiplier )

        result = 'done'

    except Exception as e:

        print(f'{Fmt.BOLD}(pcamilla) Error in config.set_active(): {str(e)}{Fmt.END}')
        result = str(e)

    if result == 'done':
        dump_config()

    return result


def dump_config(config={}, fname='camilladsp_active.yml'):
    """ This is threaded so it does not slow down
        processing configuration changes
    """

    def do_it():

        with open(f'{LOGFOLDER}/{fname}', 'w', encoding='utf-8') as f:
            yaml.dump( config,
                       f,
                       Dumper             = MyYamlIndent,
                       indent             = 2,
                       default_flow_style = False
            )

    if not config:
        config = CC.config.active()

    job = threading.Thread(target=do_it)
    job.start()


def _connect_to_camilla():

    tries = 15   # 3 sec

    while tries:
        try:
            CC.connect()
            break
        except:
            sleep(.2)
            tries -= 1

    if not tries:
        print(f'{Fmt.RED}(pcamilla) Unable to connect to CamillaDSP, check log folder.{Fmt.END}')
        return False

    return True


def check_cdsp_running(timeout=10):

    def grep_log_errors():
        with open(f'{LOGFOLDER}/camilladsp.log', 'r') as f:
            logs = f.read().strip().split('\n')
        return [l.strip() for l in logs if 'ERROR' in l]


    period = .5
    tries = int(timeout / period)

    while tries:

        if _connect_to_camilla():
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


def _prepare_eq_conv_pcms():
    """ CamillaDSP needs a new FIR filename in order to
        reload the convolver coeffs
    """
    global LAST_EQ, EQ_LINK

    EQ_LINK = f'{EQFOLDER}/eq.pcm'

    LAST_EQ = 'A'

    shutil.copy(f'{EQFOLDER}/eq_flat.pcm', f'{EQFOLDER}/eq_A.pcm')
    shutil.copy(f'{EQFOLDER}/eq_flat.pcm', f'{EQFOLDER}/eq_B.pcm')


def get_state():
    """ This is the internal camillaDSP state """
    return CC.general.state()


def _prepare_cam_config(pAudio_config):
    """
        1. Prepares a base CamillaDSP config
        2. Translates pAudio configuration to the CamillaDSP syntax

        returns: the CamillaDSP config
    """

    def clear_xo_parameters(xo):
        """ Some pAudio fields, such as XO latency and gains, should not be passed to CamillaDSP

            {   'type': 'Conv',
                'parameters': {
                    'filename': '/home/paudio/pAudio/loudspeakers/SeasFlat/48000/xo.lo.original.mp.pcm',
                    'format': 'F32_LE',
                    'type': 'Raw',
                    'latency': 0.2,
                    'flat_gain': -8.7,
                    'posit_gain': 8.7
                }
            }
        """

        xo_copy = copy.deepcopy(xo)

        xo_copy["parameters"].pop("latency",    None)
        xo_copy["parameters"].pop("flat_gain",  None)
        xo_copy["parameters"].pop("posit_gain", None)

        return xo_copy


    def prepare_outputs_structure():
        """ The multi-output N channels expander Mixer
        """

        def do_xo_stuff():
            """ This is the LAST step into the PIPELINE.
            """

            xosets = list( pAudio_config["xo"].keys() )
            print(f'{Fmt.BLUE}{Fmt.BOLD}(pcamilla) XOVER sets: {xosets}{Fmt.END}')

            # xo filters
            for set_name, ways in pAudio_config["xo"].items():
                for way, way_def in ways.items():
                    # the filter itself
                    filter_name = f'xo.{way}.{set_name}'
                    cam_config["filters"][filter_name] = clear_xo_parameters(way_def)
                    # and its corresponding gain filter (apply negative to compensate the flat_region offset)
                    g = -1 * way_def["parameters"].get('flat_gain', 0.0)
                    cam_config["filters"][f'xo.{way}.{set_name}_gain'] = make_gain_filter(g, f'gain for xo.{way}.{set_name}')

            # delay filters definition
            for out, params in pAudio_config["outputs"].items():
                if not params["name"]:
                    continue
                cam_config["filters"][f'delay.{params["name"]}'] = make_delay_filter( params["delay"], params["name"] )

            # pipeline (will use the first configured xo set inside lspk.yml)
            default_xo_set = next( iter( pAudio_config["xo"] ) )

            xo_steps = make_xover_steps( pAudio_config["outputs"], default_xo_set )

            for xo_step in xo_steps:
                cam_config["pipeline"].append(xo_step)


        def get_set_of_output_names():
            pa_outputs = pAudio_config["outputs"]
            output_names = [ pa_outputs[x]["name"] for x in pa_outputs.keys() ]
            output_names =[ x for x in set( output_names ) if x ]
            return sorted(output_names)


        # Prepare the needed expander mixer ...
        m = make_expand_mixer( pAudio_config["outputs"] )
        m_name = f'from2to{ len( pAudio_config["outputs"] ) }channels'
        cam_config["mixers"][m_name] = m
        print(f'(pcamilla) {Fmt.MAGENTA}{m_name} | {cam_config["mixers"][m_name]["description"]}{Fmt.END}')

        # Adding the mixer to the pipeline
        m_step = {  'type':         'Mixer',
                    'name':         m_name,
                    'description':  'expand LR to multi outputs'
        }
        cam_config["pipeline"].append(m_step)

        # XO OVER (pipeline filtering steps) is needed when
        # the set of outputs names is not a simple fr.L / fr.R
        if get_set_of_output_names() != ['fr.L', 'fr.R']:
            do_xo_stuff( )


    # From here `cam_config` will grow progressively
    cam_config = {}

    # CamillaDSP base config
    base_config.prepare_base_config(pAudio_config, cam_config)

    # EQ and DRC filters previously imported from the loudspeaker folder 'camilla_dsp.yml' file
    if pAudio_config.get('lspk_eq') or pAudio_config.get('drc'):
        lspk.update_lspk(pAudio_config, cam_config)

    # If more than 2 outputs it is needed to expand the pipeline
    if len( pAudio_config["outputs"] ) > 2:
        prepare_outputs_structure()


    # Dither (will apply to the lasts steps of the pipeline)
    if pAudio_config.get("coreaudio", {}).get("devices", {}).get("playback", {}).get("dither", {}):
        base_config.append_dither(pAudio_config, cam_config)

    return cam_config


def init_camilladsp(pAudio_config):
    """ Updates camilladsp.yml with user configs,
        including the auto made DRC yaml stuff.

        Then uploads the configuration to the previously
        CamillaDSP running process.

        Returns a <string>:

            'done' OR 'some problem description...'
    """

    def cpal_ports_ok(clear_cpal2system=False):
        """ Check for:

            - no weird cpal ports named like `cpal_client_in-01`

            - no cpal ports are connected to system ports (optional)

            NOTICE: all the cpal ports are bound to system ports by design

            (bool)
        """

        result = True

        try:
            jcli = jack.Client(name='tmp', no_start_server=True)

        except Exception as e:
            print(f'{Fmt.BOLD}(pcamilla) cannot open a jack client to check cpal ports: {str(e)}{Fmt.END}')
            return False

        cpal_ports = jcli.get_ports('cpal_client')

        # Early return if any 'cpal_client_in-01' or '..._out-01' is detected
        bad_ports = []
        for cpal_port in cpal_ports:
            if '-' in cpal_port.name:
                bad_ports.append(cpal_port.name)

        if bad_ports:
            print(f'{Fmt.BOLD}(pcamilla) weird CamillaDSP behavior having ports:\n    {bad_ports}{Fmt.END}')
            result = False

        if clear_cpal2system:

            # Clearing from system ports
            for cpal_port in cpal_ports:

                conns = None
                tries = 10
                while tries and not conns:

                    conns = jcli.get_all_connections( cpal_port )

                    for c in conns:
                        if 'system' in c.name:
                            jcli.disconnect(cpal_port, c)
                            print(f'{Fmt.GRAY}(pcamilla) clearing {cpal_port.name} -- {c.name}{Fmt.END}')

                    sleep(.2)
                    tries -= 1

            # Checking clearing
            for cpal_port in cpal_ports:
                conns = jcli.get_all_connections( cpal_port )
                if conns:
                    raise Exception(f'{Fmt.BOLD}(pcamilla) ERROR cannot clear: {cpal_port.name} from system port{Fmt.END}')

        jcli.close()
        del jcli

        return result


    global CC

    # Early return if connection to CamillaDSP fails
    if _connect_to_camilla():
        print(f'{Fmt.BLUE}(pcamilla) Connected to CamillaDSP websocket.{Fmt.END}')
    else:
        print(f'{Fmt.BOLD}(pcamilla) ERROR connecting to CamillaDSP websocket.{Fmt.END}')
        return

    # Prepare the camilladsp.yml as per the pAudio user configuration
    #
    cfg_init = _prepare_cam_config(pAudio_config)
    #
    # and dump it to disk
    dump_config(cfg_init, fname='camilladsp_init.yml')


    # Loading configuration
    try:

        print(f'(pcamilla) Trying to load configuration into the runnig CamillaDSP process. {Fmt.BOLD}{Fmt.BLUE}PLEASE WAIT{Fmt.END}')
        set_config_sync(cfg_init)
        # First configuration takes a bit
        sleep(.5)
        if not CC.config.active():
            raise Exception('Failed to load the config into CamillaDSP, see LOG folder')

        # Check CPAL jack ports
        if pAudio_config.get('jack'):
            if not cpal_ports_ok():
                return f'problems with CamillaDSP CPAL ports'

        # ALL IS OK
        return 'done'

    except Exception as e:

        print(f'{Fmt.BOLD}(pcamilla) ERROR loading CamillaDSP configuration. {str(e)}{Fmt.END}')
        return str(e)


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


    cfg = CC.config.active()
    cfg["filters"]["preamp_eq"]["parameters"]["filename"] = eq_path
    set_config_sync(cfg)

    toggle_last_eq()


# Setting AUDIO, allways **MUST** return some string, usually 'done'

# CAPTURE DEVICE CHANGE
def set_capture( capture_params ):
    """
        (i) This is used only for a Coreaudio multidevice config.yml setup,
            emulating a "source selector" mechanism.

            CamillaDSP can change on the fly the capture device.

            'format' is preferred to leave not specified because it is
            in charge of CoreAudio (MIDI Audio Setup)

            https://github.com/HEnquist/camilladsp/blob/master/backend_coreaudio.md

        capture_params example:

            {'channels': 2, 'device': 'USB Audio CODEC '}

    """

    c = CC.config.active()

    c["devices"]["capture"]["channels"] = capture_params["channels"]
    c["devices"]["capture"]["device"]   = capture_params["device"]
    c["devices"]["capture"]["format"]   = capture_params.get('format', None)

    # Changing the device takes more than usual
    result = set_config_sync(c, wait_multiplier=4)

    return result


# RELOAD EQ setting audio functions
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
        return f'(pcamilla.set_target) ERROR: {str(e)}'


def set_loudness( mode, level, clamp_above_zero=True):
    """ mode:   loudness compensation activation True/False

        level:  target level relative to REF_LEVEL

        clamp_above_zero:  do not apply curve for level > 0 dB
    """

    if type(mode) != bool:
        return 'must be True/False'

    if clamp_above_zero:
        level = min(level, 0)

    spl                 = level + mkeq.LOUDNESS_REF_LEVEL
    mkeq.spl            = spl
    mkeq.equal_loudness = mode

    reload_eq()

    return 'done'


# Other setting audio functions
def set_gain_offset(gain):

    try:
        gain = round(gain, 1)
    except Exception as e:
        return str(e)

    if abs(gain) > 15.0:
        return 'max gain is +/- 15 dB'

    c = CC.config.active()

    c["filters"]["source_gain_offset"]["parameters"]["gain"] = gain

    # Upload the config to runtime
    set_config_sync(c)

    return 'done'


def set_delay(delay):

    try:
        delay = round( float(delay), 1)
    except Exception as e:
        return str(e)

    if delay > 2000:
        return 'max delay is 2000 ms'

    if not delay >= 0.0:
        return 'delay must be zero or positive float'

    c = CC.config.active()

    c["filters"]["preamp_delay"]["parameters"]["delay"] = delay

    # Upload the config to runtime
    set_config_sync(c)

    return 'done'


def set_volume(dB=None, mode='abs'):
    """ get or set the Main fader volume

        mode: 'add' or 'rel' to make relative changes
    """
    try:

        if 'rel' in mode or 'add' in mode:
            dB = CC.volume.volume(0) + dB

        if dB <= 0:
            CC.volume.set_volume(0, dB)

    except Exception as e:
        print(f'(pcamilla.set_volume) ERROR: {str(e)}')

    return CC.volume.volume(0)


def set_mute(mode):

    if mode in (True, 'true', 'on', 1):
        CC.volume.set_main_mute(True)

    if mode in (False, 'false', 'off', 0):
        CC.volume.set_main_mute(False)

    if mode == 'toggle':
        new_mode = {True: False, False: True} [CC.volume.main_mute() ]
        CC.volume.set_main_mute(new_mode)

    return 'done'


def set_swap_LR(mode):

    match mode:

        case 'off'  | False:
            src_0 = 0
            src_1 = 1

        case 'on' | True:
            src_0 = 1
            src_1 = 0

        case _:
            return f'mode must be in: on | true | off | false'

    c = CC.config.active()

    curr_mapping = c["mixers"]["preamp_mixer"]["mapping"]

    curr_mapping[0]["sources"][0]["channel"] = src_0
    curr_mapping[0]["sources"][1]["channel"] = src_1
    curr_mapping[1]["sources"][0]["channel"] = src_0
    curr_mapping[1]["sources"][1]["channel"] = src_1

    set_config_sync(c)

    return 'done'


def set_midside(mode):

    modes = ('off', 'mid', 'side', 'solo_L', 'solo_R')

    if mode in modes:

        c = CC.config.active()

        if mode == 'off':
            mode = 'normal'

        c["mixers"]["preamp_mixer"] = make_mixer_preamp(midside_mode = mode)

        set_config_sync(c)

        return 'done'

    else:
        return f'mode error must be in: {modes}'


def set_solo(mode):

    match mode:

        case 'l' | 'L':
            m = make_mixer_preamp(midside_mode='solo_L')

        case 'r' | 'R':
            m = make_mixer_preamp(midside_mode='solo_R')

        case 'off':
            m = make_mixer_preamp(midside_mode='normal')

        case _:
            return 'solo mode must be in: L | R | off'

    c = CC.config.active()

    c["mixers"]["preamp_mixer"] = m

    set_config_sync(c)

    return "done"


def set_polarity(mode):
    """ Polarity applied to channels
    """
    if mode in ('normal','off'):    mode = '++'

    modes = ('++', '--', '+-', '-+')

    result = f'Polarity must be in: {modes}'

    c = CC.config.active()

    match mode:

        case '++':      inv_L = False;   inv_R = False
        case '--':      inv_L = True;    inv_R = True
        case '+-':      inv_L = False;   inv_R = True
        case '-+':      inv_L = True;    inv_R = False

    c["filters"]["bal_pol_L"]["parameters"]["inverted"] = inv_L
    c["filters"]["bal_pol_R"]["parameters"]["inverted"] = inv_R

    set_config_sync(c)

    return "done"


def set_compressor(mode):
    """ <mode> can be 'off' or a ratio indicator
        for example '2.0:1'

        returns: 'done' or an error description string
    """

    def set_ratio(ratio):
        """ ratio format must be 'float:1', example:  '3.0:1'

            returns: 'done' or an error description string
        """

        def check_ratio_format(ratio):

            if not ratio.endswith(':1'):
                return False

            try:
                float( ratio.split(':')[0] )
                return True

            except Exception as e:
                print(f'{Fmt.RED}(pcamilla) set_compressor error: {str(e)}{Fmt.END}')
                return False


        def calc_makeup_gain(fac, th=60):
            """ Estimates the make up gain for a given compression factor, that is
                a compressor ratio of "fac:1", assuming a "quasi full scale compressor"
                (threshold = -60 dB)
            """

            #experimetal_divider = 1.5
            experimetal_divider = 2.0

            return round( -(th - th / fac) / experimetal_divider, 1)


        if not check_ratio_format(ratio):
            return 'bad ratio'

        factor      = round( float( ratio.split(':')[0] ), 1)
        threshold   = -60
        makeup_gain = calc_makeup_gain(factor, threshold)

        c = CC.config.active()
        params = c["processors"]["movies_compressor"]["parameters"]
        params["threshold"]   = threshold
        params["factor"]      = factor
        params["makeup_gain"] = makeup_gain

        return set_config_sync(c)


    def bypass_compressor_step(mode):
        """ bool
            returns: 'done' or an error description string
        """
        c = CC.config.active()

        c["pipeline"][0]["bypassed"] = mode

        return set_config_sync(c)


    if mode in ('on', 'off', True, False):

        if mode == 'on' or mode == True:
            bypassed = False
        else:
            bypassed = True

        return bypass_compressor_step(bypassed)

    else:

        ans = set_ratio(mode)
        if ans == 'done':
            bypass_compressor_step(False)

        return ans


def set_balance(dB):
    """ negative dBs means towards Left, positive to Right
    """
    c = CC.config.active()
    c["filters"]["bal_pol_L"]["parameters"]["gain"] = -dB / 2.0
    c["filters"]["bal_pol_R"]["parameters"]["gain"] = +dB / 2.0

    set_config_sync(c)

    return "done"


def set_xo(xo_set):

    cfg = CC.config.active()

    # The pipeline is a LIST of steps
    for step_index, step in enumerate( cfg["pipeline"] ):

        # Example of XOVER step:
        #
        #   - bypassed: null
        #   channels:
        #   - 2
        #   description: xover.lo.L
        #   names:
        #   - xo.lo.original.mp         <--- the xo-filter itself
        #   - xo.lo.original.mp_gain    <--- there is a _gain auxiliary filter for each xo-filter
        #   - delay.lo.L                <--- also a delay
        #   type: Filter

        if step.get('description') and step.get('description')[:5] == 'xover':

            # Step names is a LIST of filter names
            for fname_index, fname in enumerate( step["names"] ):

                if fname[:2] == 'xo':

                    # the gain filter name
                    if fname[-5:] == '_gain':
                        new_fname = fname[:6] + xo_set + '_gain'
                    # the xo filter name itself
                    else:
                        new_fname = fname[:6] + xo_set

                    cfg["pipeline"][step_index]["names"][fname_index] = new_fname

    try:
        set_config_sync(cfg)
        result = 'done'

    except Exception as e:
        result = f'(pcamilla.set_xo) ERROR: {str(e)}'

    return result


def set_drc(drc_id, flat_gain=0.0):
    """
        It is supposed to receive a validated drc_id one OR 'none'

        If 'none' the program will flush any drc_xxxx
        into the pipeline step `names` field
    """

    cfg = CC.config.active()
    fnames = cfg.get('filters')

    # DRC filters are named 'drc_{drc_id}_NN_C', where:
    #   NN  number of stage (01 for FIR types, or several secuential NN for IIR types)
    #   C   channel 'L' or 'R'

    drc_fnames    = [ x for x in fnames if x[:4] == 'drc_' and x[-2:] in ('_L', '_R') ]
    drc_id_fnames = [ x for x in drc_fnames if x[3:-4] == f'_{drc_id}_' ]
    drc_id_fnames = sorted( drc_id_fnames )

    # Iterate over the pipeline steps
    for i, step in enumerate( cfg["pipeline"] ):

        # filter DRC steps
        if step.get('description') and  step.get('description', '').startswith('DRC '):

            step_ch = step["channels"][0]

            # remove any 'drc_xxxx' in `names:` (will keep 'dither' if so)
            new_names = [ x for x in step["names"] if x[:4] != 'drc_' ]

            # 'dither' must be the LAST pipeline step
            dither_pending = False
            if 'dither' in new_names:
                new_names.remove('dither')
                dither_pending = True

            # add the new drc filters in `names:`
            for fname in drc_id_fnames:
                if step_ch == 0 and fname[-2:] == '_L' or step_ch == 1 and fname[-2:] == '_R':
                    new_names.append(fname)

            if dither_pending:
                new_names.append('dither')

            cfg["pipeline"][i]["names"] = new_names

    # Adjust the global flat_gain_drc for this drc-set
    # Apply negative to compensate the flat_region offset
    cfg["filters"]["flat_gain_drc"]["parameters"]["gain"] = -flat_gain

    # Upload the config to runtime
    set_config_sync(cfg)

    return 'done'


def set_lu_offset(dB):

    cfg = CC.config.active()

    cfg["filters"]["lu_offset"]["parameters"]["gain"] = dB

    set_config_sync(cfg)

    return 'done'


    cfg = CC.config.active()

    cfg["filters"]["lu_offset"]["parameters"]["gain"] = dB

    set_config_sync(cfg)

    return 'done'


_prepare_eq_conv_pcms()
