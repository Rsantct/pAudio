#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Preamp subsystem.

    Version with CamillaDSP processor (https://github.com/HEnquist/camilladsp)

    NOTICE: This relays level related commands to the remote volume manager daemon
            (Find 'forward to remotes manager daemon' below)

"""

import  sys
import  os
import  subprocess as sp
import  json
import  threading

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

STATE["application"] = 'pAudio'


def init():

    def resume_audio():

        def print_failure(param):
            print(f'{Fmt.RED}cannot resume state.{param}={STATE[param]}: {res}{Fmt.END}')

        set_mute( True )

        # Only multiway
        if XO_SETS:
            if not STATE["xo_set"] in XO_SETS:
                STATE["xo_set"] = XO_SETS[0]
            set_xo( STATE["xo_set"] )

        # All multiway and full-range
        res = do_levels( 'level', dB=STATE["level"] )
        if res != 'done':
            print_failure('level')

        set_polarity( STATE["polarity"] )

        set_solo( STATE["solo"] )

        res = do_levels( 'balance', dB=STATE["balance"] )
        if res != 'done':
            print_failure('level')

        set_midside( STATE["midside"] )

        res = do_levels( 'bass', dB=STATE["bass"] )
        if res != 'done':
            print_failure('bass')

        res = do_levels( 'treble', dB=STATE["treble"] )
        if res != 'done':
            print_failure('treble')

        res = do_levels( 'lu_offset', dB=STATE["lu_offset"] )
        if res != 'done':
            print_failure('lu_offset')

        res = do_levels( 'target', tID=STATE["target"] )
        if res != 'done':
            print_failure('target')

        res = set_loudness( mode=STATE["equal_loudness"] )
        if res != 'done':
            print_failure('equal_loudness')

        if not STATE["drc_set"] in DRC_SETS or not STATE["drc_set"] in DRC_SETS:
            STATE["drc_set"] = 'none'

        set_drc( STATE["drc_set"] )


        # Source needs a little care
        last_source = STATE.get('source')

        if last_source and last_source in CONFIG["sources"]:

            set_source( last_source )

        else:

            if CONFIG.get('jack'):
                STATE["source"] = 'none'

            elif CONFIG.get('coreaudio'):
                # the first one as inserted
                STATE["source"] = next(iter( CONFIG["sources"] ))

            else:
                STATE["source"] = ''


        # Unmute by default
        if CONFIG.get('on_init', {}).get('keep_muted', False):
            set_mute( STATE["muted"] )
        else:
            STATE["muted"] = False
            set_mute(False)

        save_json_file(STATE, PREAMP_STATE_PATH)


    global STATE, CONFIG, TARGET_SETS, XO_SETS, DRC_SETS


    if CONFIG.get('jack'):
        CONFIG["sources"] = jack_sources.SOURCES

    elif CONFIG.get('coreaudio'):
        CONFIG["sources"] = coreaudio_sources.get_coreaudio_sources()

    else:
        CONFIG["sources"] = {}


    # Dump CONFIG to disk
    write_pAudio_cfg(CONFIG)

    # Target curve sets
    TARGET_SETS = get_target_sets(fs=CONFIG["samplerate"])

    # XO sets
    XO_SETS = list( CONFIG["xo"].keys() )

    # DRC sets
    DRC_SETS = ['none'] + list( CONFIG["drc"].keys() )

    # Default SOURCE set to 'Desktop' or 'none'
    if not STATE.get('source', '') in ('Desktop', 'none'):
        STATE["source"] = 'none'

    # ON_INIT optional user config settings having precedence over the saved state:
    for prop, value in CONFIG.get('on_init', {}).items():

        valid_props = ('source', 'level', 'balance', 'bass', 'treble', 'tone_defeat',
                       'lu_offset', 'equal_loudness', 'target', 'drc_set', 'xo_set',
                       'midside', 'mono')

        # keep_muted is processed later in resume_audio()
        if prop == 'keep_muted':
            continue

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
                    print(f'{Fmt.BOLD}(on_init) ERROR in target: {value}{Fmt.END}')

            case 'xo_set':

                if value in XO_SETS or value == 'none':
                    STATE["xo_set"]     = value
                    STATE["xo_latency"] = get_xo_latency( value )
                else:
                    print(f'{Fmt.BOLD}(on_init) ERROR in xo_set: {value}{Fmt.END}')

            case 'drc_set':

                if value in DRC_SETS or value == 'none':
                    STATE["drc_set"] = value
                else:
                    print(f'{Fmt.BOLD}(on_init) ERROR in drc_set: {value}{Fmt.END}')

            case 'midside':

                midside_values = ('off', 'mid', 'side', 'solo_L', 'solo_R')
                if value in midside_values:
                    STATE["midside"] = value
                else:
                    print(f'{Fmt.BOLD}(on_init) ERROR midside must be in: {midside_values}{Fmt.END}')

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
    STATE["samplerate"]     = CONFIG["samplerate"]
    STATE["polarity"]       = '++'
    STATE["compressor"]     = 'off'
    STATE["lr_swapped"]     = False

    # Update state with both input and output devices
    #
    if CONFIG.get('jack'):

        STATE["input_dev"]      = ''
        STATE["output_dev"]     = ''
        STATE["jack_period"]    = CONFIG["jack"]["period"]
        STATE["jack_nperiods"]  = CONFIG["jack"]["nperiods"]
        jack_buffer             = CONFIG["jack"]["period"] * CONFIG["jack"]["nperiods"]
        STATE["output_latency"] = round(jack_buffer / STATE["samplerate"] * 1000, 1)

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

        STATE["input_dev"]      = CONFIG["coreaudio"]["devices"]["capture"] ["device"]
        STATE["output_dev"]     = CONFIG["coreaudio"]["devices"]["playback"]["device"]
        STATE["output_latency"] = 0   # PENDING TO ESTIMATE BY QUERYING COREAUDIO

    else:

        STATE["input_dev"]  = 'unknown'
        STATE["output_dev"] = 'unknown'
        STATE["output_latency"] = 0

    # Update state with jack buffer if so
    if not CONFIG.get('jack'):
        try:
            keys_to_remove = [k for k in STATE if 'jack' in k]
            for k in keys_to_remove:
                del STATE[k]
        except Exception as e:
            print(f'{Fmt.RED}(preamp) error removing jack* keys inside STATE: {str(e)}{Fmt.END}')

    # Force values
    STATE["extra_delay"] = 0.0

    #
    # Initialize camillaDSP
    cdsp_init = CAM.init_camilladsp( pAudio_config=copy.deepcopy(CONFIG) )
    #

    if cdsp_init == 'done':

        STATE["dsp_buffer"]  = CAM.CC.config.active()["devices"]["chunksize"]
        STATE["dsp_latency"] = round(STATE["dsp_buffer"] / STATE["samplerate"] * 1000, 1)

        # Resuming audio settings on the CAM
        resume_audio()

        # Changing macOS playback device
        # (It will be restored when ordering `paudio.sh stop`)
        if CONFIG.get('coreaudio'):
            macos.change_default_sound_device( CONFIG["coreaudio"]["devices"]["capture"]["device"] )

        # Saving state with user settings mods
        save_json_file(STATE, PREAMP_STATE_PATH)

        # restarting loudness_monitor.py to get the current device (standalone process)
        loudness_monitor_restart()

    else:

        print(f'{Fmt.BOLD}ERROR RUNNING CamillaDSP, check:')
        print(f'    - The sound card is attached')
        print(f'    - The `config.yml` file')
        print(f'    - Logs under ~/pAudio/log/{Fmt.END}\n')

        # set a WARNING message
        camilla_error = get_camilladsp_last_error() # {date:xxx, time:xxx, error:xxx}
        send_cmd(f"ctrl warning clear", port=CONFIG["paudio_port"]+1)
        send_cmd(f"ctrl warning set {camilla_error['error']}", port=CONFIG["paudio_port"]+1)

        exit()


def eq2png():
    """  Dumping EQ to .png file non blocking
    """
    # Threading because saving the PNG file can take too long
    j1 = threading.Thread(target=fir2png)
    j1.start()


def loudness_monitor_restart():
    print(f'{Fmt.BLUE}(preamp) restarting loudness monitor.py{Fmt.END}')
    sp.Popen( f'python3 {MAINFOLDER}/code/share/loudness_monitor.py start', shell=True )


def get_xo_latency(xo_set):
    """ auxiliar to get the latency of a XO filter
        so that the STATE can be updated
    """
    latencies = [0.0]
    for band in CONFIG["xo"][xo_set].values():
        latencies.append( band["parameters"]["latency"] )
    return max(latencies)


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


def set_swap_LR(mode):
    return CAM.set_swap_LR(mode)


def rotate_compressor():
    """ returns a new compressor setting,
        within the COMPRESSOR_CYCLE values
    """

    COMPRESSOR_CYCLE = CONFIG["compressors"]

    current          = STATE["compressor"]

    # current setting may be not within the COMPRESSOR_CYCLE values
    if current in COMPRESSOR_CYCLE:
        cur_index   = COMPRESSOR_CYCLE.index(current)
    else:
        cur_index = -1

    next_index  = (cur_index + 1) % len(COMPRESSOR_CYCLE)

    new = COMPRESSOR_CYCLE[next_index]

    if set_compressor(new) == 'done':
        return new
    else:
        return current


def set_compressor(mode):
    """ returns 'done' or an error description
    """
    return CAM.set_compressor(mode)


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
            flat_gain = CONFIG["drc"][drcID].get('flat_gain', 0.0)

        res = CAM.set_drc(drcID, flat_gain)

    return res


def set_xo(xoID):

    if not XO_SETS:
        res = 'not available'

    elif not xoID in XO_SETS:
        res = f'must be in: {XO_SETS}'

    else:
        res = CAM.set_xo(xoID)

    return res


def set_source(sname):
    """ Jack and Coreaudio have different source management

        NOTICE: for remote jack sources zita buffer and compensation delay
                will be dynamically changed if config.yml has been modified
    """

    def get_zita_net_latency(dest_ip):
        """ it depends on wired or wifi, experimental values
        """
        net_link_type = get_network_type(dest_ip).lower()

        if "eth"  in net_link_type:
            return 0.4

        if "wifi" in net_link_type:
            return 2.5

        else:
            return 0.0


    def get_remote_state(rhost, rport):
        rstate = send_cmd(f'state', host=rhost, port=rport, timeout=1)
        try:
            rstate = json.loads(rstate)
        except:
            print(f'(preamp) error getting remote state')
            rstate = {'xo_set':'mp', 'xo_latency':0}
        return rstate


    def read_remote_source_config(sname):
        """ Live read the remote source config from the config.py file,
            so that on the fly configuration changes can be applied

            Example:
                { 'remote_addr':        '192.168.1.57',
                  'remote_track_level': True,
                  'zita_buffer_ms':     50
                }
        """
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)

        rem_cfg = config["jack"]["sources"].get(sname, {})

        return rem_cfg


    def do_source_settings():
        """ will order specific source settings as configured,
            otherwise will restore on_init settings if current differs,
            except for remoteXXXX sources
        """

        def do_setting(setting, value):

            ans = ''

            if setting == 'midside':
                ans = set_midside(value)

            elif setting == 'target':
                ans = do_levels('target', tID=value)

            elif setting == 'lu_offset':
                ans = do_levels('lu_offset', dB=value)

            elif setting == 'equal_loudness':
                ans = set_loudness(value)

            return ans


        if sname == 'none' or not sname or sname.startswith('remote'):
            return

        print(f'{Fmt.MAGENTA}checking specific source settings for: {sname}{Fmt.END}')

        valid_source_settings = (
            'mono', 'target', 'lu_offset', 'equal_loudness'
        )

        for setting in valid_source_settings:

            # Check if specific setting is configured:
            source_value = CONFIG["sources"].get(sname, {}).get(setting, None)

            if source_value != None:

                if setting == 'mono':
                    setting = 'midside'
                    if source_value == True:
                        source_value = 'mid'
                    else:
                        source_value = 'off'

                if do_setting(setting, source_value) == 'done':
                    print(f'{Fmt.MAGENTA}    source specific:', setting, source_value, Fmt.END)
                    STATE[setting] = source_value


            # if not, do restore the generic on_init setting if the current one differs:
            else:

                # 'mono' is a human readable alias for 'midside'
                if setting == 'mono':

                    setting = 'midside'

                    tmp = CONFIG.get('on_init', {}).get('mono', 'off')
                    if tmp in (True, 'on'):
                        on_init_value = 'mid'
                    else:
                        on_init_value = 'off'

                else:
                    on_init_value = CONFIG.get('on_init', {}).get(setting, None)

                curr_value    = STATE.get(setting, None)

                if (on_init_value != None) and (curr_value != on_init_value):

                    if do_setting(setting, on_init_value) == 'done':
                        print(f'{Fmt.GREEN2}{Fmt.BOLD}    restore on_init:', setting, on_init_value, Fmt.END)
                        STATE[setting] = on_init_value


    def order_local_and_remote_delays(ld, rd):

        def set_local():
            if set_delay( ld ) == 'done':
                STATE["extra_delay"] = round(ld, 1)
                print(f'(preamp.py) set local delay: {ld}')
            else:
                print('(preamp.py) cannot set local delay')

        def set_remote():
            if send_cmd(f'set_delay {rd}', host=remote_addr, port=remote_port) == 'done':
                print(f'(preamp.py) set remote delay: {rd}')
            else:
                print('(preamp.py) cannot set remote delay')

        j1 = threading.Thread(target=set_local)
        j2 = threading.Thread(target=set_remote)
        j1.start()
        j2.start()


    source_is_available = True

    result = 'n/a'

    if not sname in CONFIG["sources"]:
        return f'must be in: { list( CONFIG["sources"].keys() ) }'

    # COREAUDIO
    if CONFIG.get('coreaudio'):

        # CamillaDSP can change on the fly the capture device
        new_capture_parameters = CONFIG["sources"][sname]
        result = CAM.set_capture( new_capture_parameters )

        if result == 'done':
            # Capture device can change
            STATE["input_dev"] = new_capture_parameters["device"]
            # restarting loudness_monitor.py to get the current device (standalone process)
            loudness_monitor_restart()

    # JACK
    elif CONFIG.get('jack'):

        # Remote source
        if 'remote' in sname:

            # remote source settings
            rsc = read_remote_source_config(sname)
            zita_buff          = rsc.get('zita_buffer_ms', 10)
            remote_addr        = rsc.get('remote_addr')
            remote_port        = rsc.get('remote_port', 9990)
            do_track_level     = rsc.get('remote_track_level', True)
            relative_distance  = rsc.get('relative_distance', 10)

            # local behavior
            zita_net_latency = get_zita_net_latency( remote_addr )
            zita_resampler_samples = 48  # default zita value we do not override it
            local_fs = CONFIG.get('samplerate', 44100)

            lst = read_state_from_disk()
            local_dsp_latency   = lst.get('dsp_latency',    20.0)
            local_xo_latency    = lst.get('xo_latency',      0.0)
            local_out_latency   = lst.get('output_latency', 20.0)

            local_latency = (
                zita_buff + zita_net_latency + zita_resampler_samples / local_fs * 1000 +
                local_dsp_latency + local_xo_latency + local_out_latency
            )

            # remote behavior
            rst = get_remote_state(remote_addr, remote_port)
            remote_dsp_latency  = rst.get('dsp_latency',    20.0)
            remote_xo_latency   = rst.get('xo_latency',      0.0)
            remote_out_latency  = rst.get('output_latency', 20.0)

            remote_latency = (
                remote_dsp_latency + remote_xo_latency + remote_out_latency +
                relative_distance / 340 * 1000
            )

            # latency compensation: remote vs local
            latency_compensation = round( remote_latency - local_latency, 1 )

            # Tell the remote to track its volume to the local end (optional)
            if do_track_level:
                send_cmd('hello', host=remote_addr, port=remote_port + 5)

            # Remote zita-j2n sender. We force to restart zita-j2n at the sender end.
            # (the local zita-n2j is supposed to be listening from start up)
            raddr, rport, rudpport = find_zita_link_ports(sname)

            if raddr and rport and rudpport:

                ans = zita_remote_restart(raddr, rport, rudpport, 'restart').lower()

                if not ('error' in ans or 'timed out' in ans):

                    # Set local and remote delays (**)
                    if latency_compensation < 0:
                        order_local_and_remote_delays(0, abs(latency_compensation))

                    elif latency_compensation > 0:
                        order_local_and_remote_delays(latency_compensation, 0)

                    else:
                        order_local_and_remote_delays(0, 0)

                else:
                    source_is_available = False

            # Local zita-n2j receiver.
            #
            # If a new buffer setting is found under the current config.yml,
            # then we restart the local zita-n2j
            if zita_buff != CONFIG["jack"]["sources"][sname].get('zita_buffer_ms', 0):
                print(f'{Fmt.BLUE}zita-n2j appliyng new buffer: {zita_buff} ms{Fmt.END}')
                zita_local_restart(raddr, rudpport, zita_buff)
                CONFIG["jack"]["sources"][sname]["zita_buffer_ms"] = zita_buff
                write_pAudio_cfg(CONFIG)
            #
            # Anyway we check if the local zita-n2j receiver is listening from start up.
            else:
                pattern = f'zita_n2j_{ remote_addr.split(".")[-1] }'
                if not process_is_running( pattern ):
                    zita_local_restart(raddr, rudpport, zita_buff)

        if source_is_available:

            # Switch to source
            result = jack_sources.select( sname )

            # and apply gain offset (usually for analaog)
            gain = CONFIG["sources"][sname].get('gain', 0.0)
            try:
                gain = round(gain, 1)
                if set_gain_offset( gain ) == 'done':
                    STATE["source_gain_offset"] = gain
            except Exception as e:
                result = f'cannot set gain {gain} dB for source: {sname}'

            # Other source specific settings
            do_source_settings()

        else:
            result = 'source not available'

    # if not coreaudio or jack
    else:
        result = 'bad config.yml'

    # Deactivate compressor on change the source,
    # regardless source specific settings
    if set_compressor('off') == 'done':
        STATE["compressor"] = 'off'

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
            """ Positive gains of filters in use
            """

            # EQ
            lspk_eq_posit_gain = CONFIG.get('lspk_eq_posit_gain', 0.0)

            # DRC
            drc_posit_gain = 0.0
            if candidate["drc_set"] != 'none':
                drc_posit_gain = CONFIG["drc"][ candidate["drc_set"] ].get('posit_gain', 0.0)

            # XO: we need to find out the greater one involved in the xo_set (if any)
            xo_posit_gains = [0.0]
            for xo_definition in CONFIG.get('xo', {}).get(candidate["xo_set"], {}).values():
                posit_gain = xo_definition["parameters"].get('posit_gain', 0.0)
                xo_posit_gains.append( posit_gain )

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


    # --> forward to remotes manager daemon
    send_to_remotes(f'{cmd} {dB} {"add" if add else ""}')

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


def send_to_remotes(cmd):
    """ remotes are managed by remote_volume_daemon which listen at base port + 2
    """
    remotes_manager_port = CONFIG["paudio_port"] + 2
    send_cmd( cmd, port=remotes_manager_port)


# Entry function
def do(cmd, args, add):

    def get_compressor_status():
        """ returns 'off' or a ratio descriptor 'x.y:1'
        """
        cc = CAM.get_config()
        if cc["pipeline"][0].get('bypassed', False):
            return 'off'
        else:
            factor = cc["processors"]["movies_compressor"]["parameters"]["factor"]
            return f'{factor}:1'


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

        return cmd.lower()


    cmd     = normalize_cmd(cmd)
    result  = 'nothing to do'

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
            result = json.dumps( list(CONFIG["sources"].keys()) )

        case 'get_target_sets':
            result = json.dumps(TARGET_SETS)

        case 'get_drc_sets':
            result = json.dumps(DRC_SETS)

        case 'get_xo_sets':
            result = json.dumps(XO_SETS)

        # Change commands
        case 'set_delay':
            new = args
            result = set_delay(new)
            if result == 'done':
                STATE["extra_delay"] = round(float(new), 1)

        case 'signal_detected':
            # example:   signal_detected 'system' -23.4 dB peak
            jport = args.split("'")[1] if args.split("'")[1:] else ''
            new = get_source_of_jport(jport)
            result = set_source(new)
            if result in ('done', 'ordered'):
                STATE["source"] = new

        case 'set_source':
            new = args
            result = set_source(new)
            if result in ('done', 'ordered'):
                STATE["source"] = new

        case 'swap' | 'swap_lr':

            curr = STATE.get('lr_swapped', False)
            new  = None

            if args in ('on', 'true'):
                new = True
            elif args in ('off', 'false'):
                new = False
            elif args == 'toggle':
                new = not curr

            if new == None:
                result = 'must indicate: toggle | on | off'

            else:
                if curr != new:
                    result = set_swap_LR(new)

                    if result == 'done':
                        STATE["lr_swapped"] = new

        case 'mono':

            # here we need to translate to internal `midside`

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
                # --> forward to remotes manager daemon
                #     (this is managed here to ensure new_mode after a toggle command)
                send_to_remotes(f'equal_loudness {"on" if new_mode else "off"}')

        case 'set_drc':

            new = args

            if STATE["drc_set"] != new:
                result = set_drc(new)

                if result == 'done':
                    STATE["drc_set"] = new

        case 'set_xo':

            new = args

            if STATE["xo_set"] != new:
                result = set_xo( new )

                if result == 'done':
                    STATE["xo_set"]     = new
                    STATE["xo_latency"] = get_xo_latency( new )

        case 'compressor':
            # notice that the status file stores
            # 'off' or a ratio id, for example '2.5:1'

            new    = args

            if new == 'rotate':

                # rotate returns a new setting ratio or 'off'
                STATE["compressor"] = rotate_compressor()
                result = 'done'

            # off | on | x.y:1
            else:

                # set_compressor returns 'done' or an error descriptor
                result = set_compressor(new)
                if result == 'done':
                    STATE["compressor"] = get_compressor_status()

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


        # Special for cammillaDSP
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
