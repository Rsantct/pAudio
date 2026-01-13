#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Preamp subsystem.

    Version with CamillaDSP processor (https://github.com/HEnquist/camilladsp)

"""

import  sys
import  os
import  subprocess as sp
import  json

UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')
sys.path.append(f'{MAINFOLDER}/code/services/preamp_mod')

from    common      import *
from    eq_fir2png  import fir2png

import  pcamilla as CAM

if sys.platform.lower() == 'linux' and CONFIG.get('jack'):
    import  jack
    import  jack_sources

elif sys.platform.lower() == 'darwin' and CONFIG.get('coreaudio'):
    import  coreaudio_sources


# Main variable (preamplifier state)
STATE = read_json_file(PREAMP_STATE_PATH, quiet=True)
if not STATE:

    print(f'{Fmt.BOLD}(preamp) state file not found, getting default.{Fmt.END}')
    sp.call(f'cp {PREAMP_STATE_PATH}.sample {PREAMP_STATE_PATH}', shell=True)
    STATE = read_json_file(PREAMP_STATE_PATH, quiet=True)

    if not STATE:
        raise Exception('ERROR loading preamp state, exiting.')


def init():

    def get_coreaudio_source():
        """ This retrieves the source name in coreaudio,
            from the `capture:` section in config.yml
        """
        # default source
        result = 'Desktop'

        # 1. Read the 'normal' section, previously populated
        #    even if the 'alternative' syntax was used
        cap_device = CONFIG["coreaudio"]["devices"]["capture"]["device"]

        # 2. Check in there are any source entry under `capture:` in `config.yml`
        config_yml = yaml.safe_load( open(CONFIG_PATH, 'r') )

        for item, params in config_yml["coreaudio"]["devices"]["capture"].items():

            if not type(params) == dict:
                continue

            if params.get('device') == cap_device:
                result = item

        return result


    def resume_audio():

        set_mute( True )

        # Only multiway
        if XO_SETS:
            if not STATE["xo_set"] in XO_SETS:
                STATE["xo_set"] = XO_SETS[0]
            set_xo( STATE["xo_set"] )

        # All multiway and full-range
        do_levels( 'level', dB=STATE["level"] )

        set_polarity( STATE["polarity"] )

        set_solo( STATE["solo"] )

        do_levels( 'balance', dB=STATE["balance"] )

        set_midside( STATE["midside"] )

        # tones can be clamped when ordered out of range
        res = do_levels( 'bass', dB=STATE["bass"] )
        if res != 'done':
            print(f'{Fmt.BOLD}{res}{Fmt.END}')
            STATE["bass"] = x2int(res.split()[-1])

        res = do_levels( 'treble', dB=STATE["treble"] )
        if res != 'done':
            print(f'{Fmt.BOLD}{res}{Fmt.END}')
            STATE["treble"] = x2int(res.split()[-1])

        do_levels( 'lu_offset', dB=STATE["lu_offset"] )

        do_levels( 'target', tID=STATE["target"] )

        set_loudness( mode=STATE["equal_loudness"] )

        if not STATE["drc_set"] in DRC_SETS or not STATE["drc_set"] in DRC_SETS:
            STATE["drc_set"] = 'none'
        set_drc( STATE["drc_set"] )

        # Source needs a little care
        last_source = STATE.get('source')

        if last_source and last_source in SOURCES:

            set_source( last_source )

        else:

            if 'jack_sources' in sys.modules:
                STATE["source"] = 'none'

            elif 'coreaudio_sources' in sys.modules:
                STATE["source"] = get_coreaudio_source()

            else:
                STATE["source"] = ''

        set_mute( STATE["muted"] )

        save_json_file(STATE, PREAMP_STATE_PATH)


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
                    format: FLOAT32LE


                    ---------------------------------------------------------------
                    Alternative more than one section, to have source selection

                    Mac Desktop:
                        channels: 2
                        device: BlackHole 2ch
                        format: FLOAT32LE

                    TV:
                        channels: 2
                        device: UMC204HD 192k
                        format: S24LE
                    ---------------------------------------------------------------


                playback:

                    channels: 2
                    device: Altavoces del MacBook Pro
                    format: FLOAT32LE

        --> If the ALTERNATIVE syntax was used, we complete the normal syntax here,
            taking the first device found.

        """


        # If 'alternative' syntax was used,
        # we need to generate a 'normal' capture section
        if not CONFIG["coreaudio"]["devices"]["capture"].get('device'):

            in_devices = CONFIG["coreaudio"]["devices"].get('capture')

            first_in_device, first_in_device_params = next( iter( in_devices.items() ) )

            # Adding the 'normal' capture section
            CONFIG["coreaudio"]["devices"]["capture"] = first_in_device_params


    global STATE, CONFIG, SOURCES, TARGET_SETS, XO_SETS, DRC_SETS


    # (i) SOURCES can be populated internally with known plugins,
    #     so the configured YAML should only contain user-defined sources.
    if 'jack_sources' in sys.modules:
        SOURCES = jack_sources.SOURCES

    elif 'coreaudio_sources' in sys.modules:
        SOURCES = coreaudio_sources.SOURCES

    else:
        SOURCES = {}

    CONFIG["sources"] = SOURCES

    # Dump CONFIG to disk
    with open(f'{LOGFOLDER}/pAudio_cfg', 'w') as f:
        #f.write( yaml.dump(CONFIG, default_flow_style=False, sort_keys=False, indent=2) )
        f.write( json.dumps(CONFIG, indent=2) )

    # Target curve sets
    TARGET_SETS = get_target_sets(fs=CONFIG["samplerate"])

    # XO sets
    XO_SETS = list( CONFIG["xo"].keys() )

    # DRC sets
    DRC_SETS = ['none'] + list( CONFIG["drc"].keys() )

    # Default SOURCE set to 'Desktop' or 'none'
    if not STATE["source"] in ('Desktop', 'none'):
        STATE["source"] = 'none'

    # ON_INIT optional user config settings having precedence over the saved state:
    for prop, value in CONFIG.get('on_init', {}).items():

        valid_props = ('source', 'level', 'balance', 'bass', 'treble', 'tone_defeat',
                       'lu_offset', 'equal_loudness', 'target', 'drc_set',
                       'mid_side', 'mono' )

        if not prop in valid_props:
            print(f'{Fmt.BOLD}(on_init) NOT valid: `{prop}`{Fmt.END}')
            continue

        if value == None:
            continue

        # Some validation
        match prop:

            case 'target':

                if value in TARGET_SETS + ['none']:
                    STATE["target"] = value
                else:
                    print(f'{Fmt.BOLD}(on_init) ERROR in target{Fmt.END}')

            case 'drc_set':

                if value in DRC_SETS or value == 'none':
                    STATE["drc_set"] = value
                else:
                    print(f'{Fmt.BOLD}(on_init) ERROR in drc_set{Fmt.END}')

            case 'mid_side':

                mid_side_values = ('off', 'mid', 'side', 'solo_L', 'solo_R')
                if value in mid_side_values:
                    STATE["midside"] = value
                else:
                    print(f'{Fmt.BOLD}(on_init) ERROR mid_side must be in: {mid_side_values}{Fmt.END}')

            case 'mono':

                mono_values = ('off', 'on', True, False)

                if value in mono_values:
                    if value == 'on' or value == True:
                        value = 'mid'
                    else:
                        value = 'off'
                    STATE["midside"] = value

                else:
                    print(f'{Fmt.BOLD}(on_init) ERROR mono must be in: {mono_values}{Fmt.END}')

            case _:

                STATE[prop] = value


    # Forced init settings
    STATE["loudspeaker"]    = CONFIG["loudspeaker"]
    STATE["fs"]             = CONFIG["samplerate"]
    STATE["polarity"]       = '++'


    # Update state with both input and output devices
    #
    if CONFIG.get('jack'):

        STATE["jack_buffer_size"] = CONFIG["jack"]["period"] * CONFIG["jack"]["nperiods"]
        STATE["jack_buffer_ms"]   = int(round(STATE["jack_buffer_size"] / STATE["fs"] * 1000))
        STATE["input_dev"]        = ''
        STATE["output_dev"]       = ''

        # open a temporary jack.Client
        try:
            jcli = jack.Client(name='tmp', no_start_server=True)

            if jcli.get_ports('system', is_physical=True, is_output=True):
                STATE["input_dev"]  = CONFIG["jack"]["device"]

            if jcli.get_ports('system', is_physical=True, is_input=True):
                STATE["output_dev"]  = CONFIG["jack"]["device"]

            jcli.close()
            del jcli

        except Exception as e:
            print(f'{Fmt.RED}(preamp) init, cannot open a jack client to chek i/o devices: {str(e)}{Fmt.END}')


    elif CONFIG.get('coreaudio'):

        # 1st we need to prepare Coreaudio capture section, see above funcion
        prepare_coreaudio_init_devices()

        STATE["input_dev"]  = CONFIG["coreaudio"]["devices"]["capture"] ["device"]
        STATE["output_dev"] = CONFIG["coreaudio"]["devices"]["playback"]["device"]

    else:
        STATE["input_dev"]  = 'unknown'
        STATE["output_dev"] = 'unknown'

    # Update state with jack buffer if so
    if not CONFIG.get('jack'):
        try:
            del STATE["jack_buffer_size"]
            del STATE["jack_buffer_ms"]
        except:
            pass


    # Force values
    STATE["dsp_buffer_size"] = 0
    STATE["extra_delay"] = 0

    # Initialize camillaDSP
    cdsp_init = CAM.init_camilladsp( pAudio_config=CONFIG )

    if cdsp_init == 'done':

        STATE["dsp_buffer_size"] = CAM.CC.config.active()["devices"]["chunksize"]
        STATE["dsp_buffer_ms"]   = int(round(STATE["dsp_buffer_size"] / STATE["fs"] * 1000))

        # Resuming audio settings on the CAM
        resume_audio()

        # Changing macOS playback device
        # (It will be restored when ordering `paudio.sh stop`)
        if CONFIG.get('coreaudio'):
            macos.change_default_sound_device( CONFIG["coreaudio"]["devices"]["capture"]["device"] )

        # Saving state with user settings mods
        save_json_file(STATE, PREAMP_STATE_PATH)

    else:

        print(f'{Fmt.BOLD}ERROR RUNNING CamillaDSP, check:')
        print(f'    - The sound card is attached')
        print(f'    - The `config.yml` file')
        print(f'    - Logs under ~/pAudio/log/{Fmt.END}\n')

        # set a WARNING message
        camilla_error = get_camilladsp_last_error() # {date:xxx, time:xxx, error:xxx}
        send_cmd(f"ctrl warning clear", port=PAUDIO_PORT+1)
        send_cmd(f"ctrl warning set {camilla_error['error']}", port=PAUDIO_PORT+1)

        sys.exit()


def eq2png():
    """  Dumping EQ to .png file and alerting clients to let them know
    """

    def alert_new_eq_graph(timeout=1):
        """ This sets the 'new_eq_graph' field to True for a while
            so that the web page can realize when the graph is dumped.
            This helps on slow machines because the PNG graph takes a while
            after the 'done' is received when issuing some audio command.
        """

        def new_eq_graph(mode):
            aux_info = read_json_file(AUXINFO_PATH)
            aux_info['new_eq_graph'] = mode
            save_json_file(aux_info, AUXINFO_PATH)

        def mytimer(timeout):
            sleep(timeout)
            new_eq_graph(False)

        new_eq_graph(True)

        job = threading.Thread(target=mytimer, args=(timeout,))
        job.start()


    def do_graph(e):
        fir2png()
        e.set()


    def flag_to_aux_info(e):
        e.wait()    # waits until set flag is true
        alert_new_eq_graph()


    # Threading because saving the PNG file can take too long
    e  = threading.Event()
    j1 = threading.Thread(target=do_graph,         args=(e,))
    j2 = threading.Thread(target=flag_to_aux_info, args=(e,))
    j1.start()
    j2.start()


# Interface functions with the underlying modules

def set_gain_offset(gain):
    return CAM.set_gain_offset(gain)


def set_delay(delay):
    return CAM.set_delay(delay)


def set_mute(mode):
    return CAM.set_mute(mode)


def set_solo(mode):
    return CAM.set_solo(mode)


def set_midside(mode):
    return CAM.set_midside(mode)


def set_polarity(mode):
    return CAM.set_polarity(mode)


def set_loudness(mode, level=STATE["level"]):
    result = CAM.set_loudness(
        mode,
        level,
        clamp_above_zero = not CONFIG["loudness_compensation_above_zero"]
    )
    return result


def set_drc(drcID):

    if not DRC_SETS:
        res = 'not available'

    elif not drcID in DRC_SETS:
        res = f'must be in: { DRC_SETS }'

    else:
        if drcID == 'none':
            flat_gain = 0.0
        else:
            flat_gain = CONFIG["drc_gains"][drcID].get('flat_gain', 0.0)

        res = CAM.set_drc(drcID, flat_gain)

    return res


def set_xo(xoID):

    if not XO_SETS:
        res = 'not available'

    elif not xoID in XO_SETS:
        res = f'must be in: {XO_SETS}'

    else:

        flat_gains = {}

        for x, gains in CONFIG["xo_gains"].items():

            # set slice
            if x[3:] == xoID:
                flat_gains[x] = gains["flat_gain"]

        res = CAM.set_xo(xoID, flat_gains)

    return res


def set_source(sname):
    """ Jack and Coreaudio have different source management
    """

    source_is_available = True
    result = 'no changes'

    if not sname in SOURCES:
        return f'must be in: { list( SOURCES.keys() ) }'

    # COREAUDIO
    if CONFIG.get('coreaudio'):

        # 'Desktop' is used when there are no alternative capture devices in config.yml
        if sname == 'Desktop':
            return 'no change available'

        res = CAM.set_capture( SOURCES[sname] )

        # Extra in coreaudio update STATE.input_dev
        config_yml         = yaml.safe_load( open(CONFIG_PATH, 'r') )
        STATE["input_dev"] = config_yml["coreaudio"]["devices"]["capture"][sname]["device"]
        save_json_file(STATE, PREAMP_STATE_PATH)


    # JACK
    elif CONFIG.get('jack'):

        # Remote source
        if 'remote' in sname:

            # Example:
            # 'remoteSalon': {  'local_delay': 5,
            #                   'remote_delay': 0,
            #                   'remote_track_level': True,
            #                   'ip': '192.168.1.57',
            #                   'port': 9990,
            #                   'jport': 'zita_n2j_57'  }

            remote_ip    = SOURCES[sname].get('ip')
            remote_port  = SOURCES[sname].get('port', 9990)
            remote_delay = SOURCES[sname].get('remote_delay', 0)

            # Tell the remote to track its volume to the local end (optional)
            if SOURCES[sname].get('remote_track_level'):
                send_cmd('hello', host=remote_ip, port=remote_port + 5)

            # We force to restart zita-j2n at sender end.
            # (the local zita-n2j is supposed to be listening from start up)
            raddr, rport, rudpport = find_zita_link_ports(sname)

            if raddr and rport and rudpport:

                ans = remote_zita_restart(raddr, rport, rudpport, 'restart').lower()

                if not ('error' in ans or 'timed out' in ans):

                    # Remote delay (optional)
                    if remote_delay:
                        send_cmd(f'add_delay {remote_delay}', host=remote_ip, port=remote_port)

                    # Prepare the local volume as the remote side
                    tmp = send_cmd(f'state', host=remote_ip, port=remote_port)
                    try:
                        rem_vol = tmp.get('level', -30)
                    except:
                        rem_vol = -30
                    send_cmd( f'preamp level {rem_vol}' )

                else:
                    source_is_available = False

        # Delay ms (optional)
        delay = SOURCES[sname].get('local_delay', 0.0)
        if set_delay( delay ) == 'done':
            STATE["extra_delay"] = delay

        if source_is_available:

            # Switch to source
            result = jack_sources.select( sname )

            # and apply gain offset (usually for analaog)
            gain = SOURCES[sname].get('gain', 0.0)
            try:
                gain = round(gain, 1)
                if set_gain_offset( gain ) == 'done':
                    STATE["source_gain_offset"] = gain
            except Exception as e:
                result = f'cannot set gain {gain} dB for source: {sname}'

        else:
            result = 'source not available'

    # if not coreaudio or jack
    else:
        result = 'bad config.yml'


    return result


def do_levels(cmd, dB=0.0, tID='+0.0-0.0', tone_defeat='False', add=False):
    """ Level related commands
    """

    def set_level(dB):
        CAM.set_volume(dB + CONFIG["ref_level_gain_offset"] )
        return set_loudness(mode=STATE["equal_loudness"], level=dB)


    def set_balance(dB):
        return CAM.set_balance(dB)


    def set_lu_offset(dB):
        return CAM.set_lu_offset(-dB)


    def set_bass(dB):
        if not STATE["tone_defeat"]:
            return CAM.set_bass(dB)
        else:
            return "done"


    def set_treble(dB):
        if not STATE["tone_defeat"]:
            return CAM.set_treble(dB)
        else:
            return "done"


    def set_target(tID):
        return CAM.set_target(tID)


    def set_tone_defeat(mode):
        res = []
        if mode == True:
            res.append( CAM.set_bass(   0.0 ) )
            res.append( CAM.set_treble( 0.0 ) )
        else:
            res.append( CAM.set_bass(   STATE["bass"]   ) )
            res.append( CAM.set_treble( STATE["treble"] ) )
        res = ' '.join( set(res) )
        return res


    def calc_headroom():

        def get_positive_gains():
            """ Used filters positive gains
            """

            # EQ
            lspk_eq_posit_gain = CONFIG.get('lspk_eq_posit_gain', 0.0)

            # DRC
            drc_posit_gain = 0.0
            if candidate["drc_set"] != 'none':
                drc_posit_gain = CONFIG["drc_gains"][ candidate["drc_set"] ]["posit_gain"]

            # XO: we need to find out the greater one involved in the xo_set
            xo_posit_gains = [0.0]

            if CONFIG.get('xo_gains'):

                for filter_name, gains in CONFIG["xo_gains"].items():

                    set_name = filter_name[3:]

                    if set_name == candidate["xo_set"]:
                        xo_posit_gains.append( gains.get('posit_gain', 0.0) )

            return  lspk_eq_posit_gain + drc_posit_gain + max( xo_posit_gains )


        candidate = STATE.copy()

        # avoid incoherent state, for example if drc files were renamed
        if not candidate["drc_set"] in CONFIG["drc"]:
            candidate["drc_set"] = 'none'

        if cmd == 'target':
            candidate['target'] = tID
        else:
            candidate[cmd] = dB


        hr = - candidate["level"]                   \
             + candidate["lu_offset"]               \
             - CONFIG["ref_level_gain_offset"]      \
             - abs(candidate["balance"]) / 2.0      \
             - get_positive_gains()


        if not candidate["tone_defeat"]:

            if candidate["bass"] > 0:
                hr -= candidate["bass"]

            if candidate["treble"] > 0:
                hr -= candidate["treble"]

        if candidate["target"] != 'none':
            tgain = x2float( candidate["target"][:4] )
            if tgain > 0:
                hr -= tgain

        return round(hr, 1)


    # getting absolute values from relative command
    if add:
        dB += STATE[cmd]

    clamped = ''
    tmax = CONFIG["tones_span_dB"]
    if cmd in ('bass', 'treble'):
        if abs(dB) > tmax:
            dB = max(-tmax, min(+tmax, dB))
            clamped = str(dB)

    hr = calc_headroom()

    if hr >= 0:

        match cmd:

            case 'level':
                result = set_level(dB)

            case 'balance':
                result = set_balance(dB)

            case 'lu_offset':
                result = set_lu_offset(dB)

            case 'bass':
                result = set_bass(dB)
                if result != 'done':
                    dB = x2int( result.split()[-1])
                    clamped = str(dB)
                    result = 'done'

            case 'treble':
                result = set_treble(dB)
                if result != 'done':
                    dB = x2int( result.split()[-1])
                    clamped = str(dB)
                    result = 'done'

            case 'tone_defeat':
                result = set_tone_defeat(tone_defeat)

            case 'target':
                result = set_target(tID)

    else:
        result = 'no headroom'

    if result == 'done':

        if cmd == 'target':
            STATE['target'] = tID

        elif cmd == 'tone_defeat':
            STATE["tone_defeat"] = tone_defeat

        else:
            STATE[cmd] = dB

        STATE["gain_headroom"] = hr

        # dumps eq to png
        eq2png()

    if clamped:
        result =  f'clamped to {dB}'

    return result


# Entry function
def do(cmd, args, add):

    def normalize_cmd(cmd):
        """ Some alias are accepted for some commands """
        try:
            cmd = {
                    'loudness':     'equal_loudness',
                    'set_target':   'target',
                    'drc':          'set_drc',
                    'xo':           'set_xo',
                    'input':        'set_source',
                    'source':       'set_source',
            }[cmd]
        except:
            pass
        return cmd


    cmd     = normalize_cmd(cmd)
    result  = 'nothing was done'

    if cmd == 'state' or cmd.startswith('get_'):
        dosave = False
    else:
        dosave = True

    match cmd:

        # Query commands
        case 'hello' | 'hi':
            result = 'preamp'

        case 'state':
            result = json.dumps(STATE, indent=2)

        case 'get_sources':
            result = json.dumps( list(SOURCES.keys()) )

        case 'get_target_sets':
            result = json.dumps(TARGET_SETS)

        case 'get_drc_sets':
            result = json.dumps(DRC_SETS)

        case 'get_xo_sets':
            result = json.dumps(XO_SETS)

        # Change commands
        case 'add_delay':
            new = args
            result = set_delay(new)
            if result == 'done':
                STATE["extra_delay"] = round(float(new), 1)

        case 'set_source':
            new = args
            result = set_source(new)
            if result in ('done', 'ordered'):
                STATE["source"] = new

        case 'mono':

            # here we need to transate to internal `midside`

            result = 'needs: on | off | toggle'

            match args:

                case 'on':
                    new = 'mid'
                    result = set_midside(new)

                case 'off':
                    new = 'off'
                    result = set_midside(new)

                case 'toggle':
                    curr = STATE["midside"]
                    new = {'off': 'mid', 'mid': 'off', 'side': 'off'}[curr]
                    result = set_midside(new)

            if result == 'done':
                STATE["midside"] = new

        case 'midside':

            new = args

            if STATE["midside"] != new:
                result = set_midside(new)

                if result == 'done':
                    STATE["midside"] = new

        case 'solo':

            new = args.lower()

            if not new in STATE["solo"]:
                result = set_solo(new)

                if result == 'done':
                    STATE["solo"] = new

        case 'polarity':

            new = args

            if STATE["polarity"] != new:
                result = set_polarity(new)

                if result == 'done':
                    STATE["polarity"] = new

        case 'mute':

            curr =  STATE['muted']
            new = switch(args, curr)

            if type(new) == bool and new != curr:
                result = set_mute(new)

            if result == 'done':
                STATE['muted'] = new

        case 'equal_loudness':

            curr_mode =  STATE['equal_loudness']
            new_mode = switch(args, curr_mode)

            if type(new_mode) == bool and new_mode != curr_mode:
                result = set_loudness(mode=new_mode)

            if result == 'done':
                STATE['equal_loudness'] = new_mode
                # dumps eq to png
                eq2png()

        case 'set_drc':

            new = args

            if STATE["drc_set"] != new:
                result = set_drc(new)

                if result == 'done':
                    STATE["drc_set"] = new

        case 'set_xo':

            new = args

            if STATE["xo_set"] != new:
                result = set_xo(new)

                if result == 'done':
                    STATE["xo_set"] = new

        # Level related commands
        # NOTICE that STATE will be updated by do_levels()
        case 'level' | 'lu_offset' | 'bass' | 'treble' | 'balance':

            try:
                dB = x2float(args)
                result = do_levels(cmd, dB=dB, add=add)

            except:
                result = 'value error'

        case 'target':

            newt = args

            if newt in TARGET_SETS + ['none']:
                if STATE["target"] != newt:
                    result = do_levels('target', tID=newt)

        case 'tone_defeat':

            curr =  STATE['tone_defeat']
            new = switch(args, curr)

            if type(new) == bool and new != curr:
                result = do_levels('tone_defeat', tone_defeat=new)


        # Special commands when using cammillaDSP
        case 'get_cdsp_config':
            result = CAM.get_config()

        case 'get_cdsp_preamp_mixer':
            result = CAM.get_config()["mixers"]["preamp_mixer"]

        case 'get_cdsp_pipeline':
            result = CAM.get_config()["pipeline"]

        case _:
            result = 'unknown command'

    if dosave:
        save_json_file(STATE, PREAMP_STATE_PATH)

    if type(result) != str:
        try:
            result = json.dumps(result)
        except Exception as e:
            result = f'Internal error: {e}'

    return result


init()
