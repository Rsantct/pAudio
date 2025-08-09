#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a CC based personal audio system.

import  os
import  sys
import  shutil
import  subprocess      as      sp
from    time            import  sleep
import  yaml
import  json
from    camilladsp      import  CamillaClient

import  make_eq         as      mkeq

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from    common import *

from    pcamilla_mod.do_makes       import  *
from    pcamilla_mod.do_clears      import  *
import  pcamilla_mod.lspk_iir       as lspk_iir
import  pcamilla_mod.base_config    as base_config

lspk_iir.Fmt         =  Fmt
base_config.Fmt      =  Fmt
base_config.EQFOLDER =  EQFOLDER


if sys.platform == 'linux' and CONFIG.get('jack'):
    import  jack


# The CamillaDSP client
HOST = '127.0.0.1'
PORT = 1234
CC   = CamillaClient(HOST, PORT)

# Optional to dump active config to disk
DUMP_ACTIVE = True

#######################################################33##########
# (!) use ALWAYS THIS FUNCTION to load a new config into CamillaDSP
###################################################################
def set_config_sync(cfg, wait=0.1):
    """ (i) When ordering set config some time is needed to be running
        This is a fake sync, but just works  >:-)
    """
    CC.config.set_active(cfg)

    if DUMP_ACTIVE:
        with open(f'{LOGFOLDER}/camilladsp_active.yml', 'w') as f:
            yaml.safe_dump(cfg, f)

    sleep(wait)


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


def get_config():
    return CC.config.active()


def _prepare_cam_config(pAudio_config):
    """
        1. Prepares a base CamillaDSP config
        2. Translates pAudio configuration to the CamillaDSP config
    """

    def prepare_multiway_structure():
        """ The multiway N channel expander Mixer
        """

        def do_xo_stuff():
            """ This is the LAST step into the PIPELINE.
            """

            xo_filters = get_xo_filters_from_loudspeaker_folder()

            if xo_filters:
                print(f'{Fmt.BLUE}{Fmt.BOLD}Found loudspeaker XOVER filter PCMs: {xo_filters}{Fmt.END}')

            else:
                print(f'{Fmt.BOLD}{Fmt.BLINK}Loudspeaker xover PCMs NOT found{Fmt.END}')


            # xo filters
            for xo_filter in xo_filters:

                cam_config["filters"][f'xo.{xo_filter}'] = make_xo_filter(  xo_filter,
                                                                            pAudio_config["samplerate"],
                                                                            LSPKFOLDER
                                                                          )

            # Auxiliary delay filters definition
            for _, pms in pAudio_config["outputs"].items():

                if not pms["name"]:
                    continue

                cam_config["filters"][f'delay.{pms["name"]}'] = make_delay_filter(pms["delay"])

            # pipeline
            if xo_filters:

                xo_steps = make_xover_steps( pAudio_config["outputs"] )

                for xo_step in xo_steps:
                    cam_config["pipeline"].append(xo_step)


        # Prepare the needed expander mixer ...
        m          = make_mixer_multi_way( pAudio_config["outputs"] )
        mixer_name = f'from2to{ len(m["mapping"]) }channels'
        cam_config["mixers"][mixer_name] = m
        #
        print(f'{Fmt.GREEN}{mixer_name} | {cam_config["mixers"][mixer_name]["description"]}{Fmt.END}')
        #
        # ... and adding it to the pipeline
        mwm_step = {'type': 'Mixer', 'name': mixer_name}
        cam_config["pipeline"].append(mwm_step)

        # The final step in the pipeline: XO
        do_xo_stuff()


    # pAudio config DEBUG
    #print('--- pAudio ----')
    #print( yaml.dump(pAudio_config, default_flow_style=False, sort_keys=False, indent=2) )

    # From here `cam_config` will grow progressively
    cam_config = {}

    # CamillaDSP base config
    base_config.prepare_base_config(pAudio_config, cam_config)

    # IIR EQ filters previously imported from the loudspeaker folder 'camilla_dsp.yml' file
    if pAudio_config.get('iir_eq'):
        lspk_iir.update_lspk_iir(pAudio_config, cam_config)

    # Multiway if more than 2 outputs
    outputs_in_use = [ x for x in pAudio_config["outputs"] if pAudio_config["outputs"][x].get('name') ]
    if len(outputs_in_use) > 2:
        prepare_multiway_structure()

    # Dither
    base_config.update_dither(pAudio_config, cam_config)

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

            s = CC.general.state()
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


    global CC

    # Prepare the camilladsp.yml as per the pAudio user configuration
    cfg_init = _prepare_cam_config(pAudio_config)

    # Dumping init config
    with open(f'{LOGFOLDER}/camilladsp_init.yml', 'w') as f:
        yaml.safe_dump(cfg_init, f)
    if DUMP_ACTIVE:
        with open(f'{LOGFOLDER}/camilladsp_active.yml', 'w') as f:
            yaml.safe_dump(cfg_init, f)


    # Stop if any process running
    sp.call('pkill -KILL camilladsp'.split())

    # Starting CamillaDSP (MUTED)
    print(f'{Fmt.BLUE}Logging CamillaDSP to log/camilladsp.log ...{Fmt.END}')
    cdsp_cmd = f'camilladsp --wait -m -a 127.0.0.1 -p 1234 ' + \
               f'--logfile "{LOGFOLDER}/camilladsp.log"'
    p = sp.Popen( cdsp_cmd, shell=True )
    sleep(1)


    # Early return if connection to CamillaDSP fails
    if _connect_to_camilla():
        print(f'{Fmt.BLUE}Connected to CamillaDSP websocket.{Fmt.END}')
    else:
        print(f'{Fmt.BOLD}ERROR connecting to CamillaDSP websocket.{Fmt.END}')
        return str(e)


    # Loading configuration
    try:
        print(f'Trying to load configuration and run.')
        CC.config.set_active(cfg_init)

        if check_cdsp_running(timeout=5):

            # Check CPAL jack ports
            if pAudio_config.get('jack'):
                if not cpal_ports_ok():
                    return f'problems with Camilla DSP CPAL ports'

            # ALL IS OK
            return 'done'

        else:
            return f'Cannot start `camilladsp` process, see `pAudio/log`'

    except Exception as e:

        print(f'{Fmt.BOLD}ERROR loading CamillaDSP configuration. {str(e)}{Fmt.END}')
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


# Getting AUDIO

def get_drc_gain():
    return json.dumps( CC.config.active()["filters"]["drc_gain"] )


# Setting AUDIO, allways **MUST** return some string, usually 'done'

# SOURCE SELECTOR function
def set_capture( source ):

    c = CC.config.active()

    c["devices"]["capture"]["channels"] = source["channels"]
    c["devices"]["capture"]["device"]   = source["device"]
    c["devices"]["capture"]["format"]   = source["format"]

    set_config_sync(c)

    return "done"


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


def set_loudness(mode, level):

    if type(mode) != bool:
        return 'must be True/False'

    spl                 = level + mkeq.LOUDNESS_REF_LEVEL
    mkeq.spl            = spl
    mkeq.equal_loudness = mode

    reload_eq()

    return 'done'


# Other setting audio functions
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

    c = CC.config.active()

    match mode:
        case 'l' | 'L': m = make_mixer_preamp(midside_mode='solo_L')
        case 'r' | 'R': m = make_mixer_preamp(midside_mode='solo_R')
        case 'off':     m = make_mixer_preamp(midside_mode='normal')
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


def set_balance(dB):
    """ negative dBs means towards Left, positive to Right
    """
    c = CC.config.active()
    c["filters"]["bal_pol_L"]["parameters"]["gain"] = -dB / 2.0
    c["filters"]["bal_pol_R"]["parameters"]["gain"] = +dB / 2.0

    set_config_sync(c)

    return "done"


def set_xo(xo_set):
    """ xo_set:     mp | lp
    """

    cfg = CC.config.active()

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
        result = f'(pcamilla.set_xo) ERROR: {str(e)}'

    return result


def set_drc(drcID):

    result = 'WIP'

    return result


def set_drc_gain(dB):

    cfg = CC.config.active()

    cfg["filters"]["drc_gain"]["parameters"]["gain"] = dB

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
