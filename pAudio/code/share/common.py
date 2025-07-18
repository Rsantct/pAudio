
#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  subprocess as sp
import  threading
import  socket
from    time import sleep
import  yaml
import  json
from    fmt import Fmt
import  sys
import  os
import  ipaddress
from    getpass import getuser

USER                = getuser()

UHOME = os.path.expanduser('~')

MAINFOLDER          = f'{UHOME}/pAudio'
LSPKSFOLDER         = f'{MAINFOLDER}/loudspeakers'
LSPKFOLDER          = f''
LOUDSPEAKER         = f''   # to be found when loading CONFIG
EQFOLDER            = f'{MAINFOLDER}/eq'
CODEFOLDER          = f'{MAINFOLDER}/code'
CONFIG_PATH         = f'{MAINFOLDER}/config.yml'
LOGFOLDER           = f'{MAINFOLDER}/log'
PLUGINSFOLDER       = f'{MAINFOLDER}/code/share/plugins'

LDCTRL_PATH         = f'{MAINFOLDER}/.loudness_control'
LDMON_PATH          = f'{MAINFOLDER}/.loudness_monitor'
AUXINFO_PATH        = f'{MAINFOLDER}/.aux_info'
PLAYER_META_PATH    = f'{MAINFOLDER}/.player_metadata'


try:
    os.mkdir(LOGFOLDER)
except:
    pass

CONFIG = {}


def init():

    def reformat_PEQ():
        """ PEQa are given in NON standard YML, having 3 fields. Example:

            PEQ:
                L:
                    #   freq    gain    Q
                    1:  123     -2.0    1.0
                    2:  456     -3.0    0.5
                R:
                    ...

            Here will convert the Human Readable fields into a dictionary.
        """

        def check_peq_params(params):

            freq, gain, q = params

            freq = float(freq)
            gain = float(gain)
            q    = float(q)

            if freq < 20.0 or freq > 20e3:
                raise Exception('Freq must be 20 ~ 20000 (Hz)')

            if gain < -20 or gain > 6:
                raise Exception('Gain must be in -20.0 ~ +6.0 (dB)')

            if q < 0.1 or q > 10:
                raise Exception('Q must be in 0.1 ~ 10')

            return freq, gain, q


        # Filling the empty keys
        if not 'PEQ' in CONFIG or not CONFIG["PEQ"]:
            CONFIG["PEQ"] = {'L': {}, 'R': {}}
        if not 'L' in CONFIG["PEQ"]:
            CONFIG["PEQ"]["L"] = {}
        if not 'R' in CONFIG["PEQ"]:
            CONFIG["PEQ"]["R"] = {}

        # PEQ parameters
        for ch in CONFIG["PEQ"]:

            if not ch in ('L', 'R'):
                raise Exception('PEQ channel must be `L` or `R`')

            if not CONFIG["PEQ"][ch]:
                CONFIG["PEQ"][ch] = {}

            for peq, params in CONFIG["PEQ"][ch].items():

                # It is expected 3 fields
                params = params.split()
                if len(params) != 3:
                    raise Exception(f'Bad PEQ #{peq}')

                # Redo in dictionary form
                freq, gain, q = check_peq_params(params)
                params = {  'freq':     freq,
                            'gain':     gain,
                            'q':        q       }

                CONFIG["PEQ"][ch][peq] = params


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
            outputs = CONFIG["outputs"]

            L_outs  = [ pms["name"] for o, pms in outputs.items()
                        if pms["name"] and pms["name"][-1]=='L' ]
            R_outs  = [ pms["name"] for o, pms in outputs.items()
                        if pms["name"] and pms["name"][-1]=='R' ]

            if len(L_outs) != len(R_outs):
                raise Exception('Number of outputs for L and R does not match')


        # A simple stereo I/O configuration if not defined
        if not 'outputs' in CONFIG:
            CONFIG["outputs"] = {1: 'fr.L', 2: 'fr.R'}

        # Outputs
        for out, params in CONFIG["outputs"].items():

            # It is expected 4 fields
            params = params.split() if params else []
            params += [''] * (4 - len(params))

            # Redo in dictionary form
            if not any(params):
                params = {  'name':     '',
                            'gain':     0.0,
                            'polarity': '+',
                            'delay':    0.0     }

            else:
                _, p = check_output_params(out, params)
                name, gain, pol, delay = p
                params = {  'name':     name,
                            'gain':     gain,
                            'polarity': pol,
                            'delay':    delay   }

            CONFIG["outputs"][out] = params

        # Check L/R pairs
        check_output_names()


    global CONFIG, LOUDSPEAKER, LSPKFOLDER

    CONFIG = read_yaml_file(CONFIG_PATH)

    if 'loudspeaker' in CONFIG:
        LOUDSPEAKER = CONFIG["loudspeaker"]
    else:
        LOUDSPEAKER = 'generic_loudspk'
        CONFIG["loudspeaker"] = LOUDSPEAKER

    LSPKFOLDER = f'{LSPKSFOLDER}/{LOUDSPEAKER}'
    if not os.path.isdir(LSPKFOLDER):
        os.mkdir(LSPKFOLDER)


    CONFIG["DSP"] = get_DSP_in_use()

    #
    # Default values if omited parameters
    #
    if not "samplerate" in CONFIG:
        CONFIG["samplerate"] = 44100
        print(f'{Fmt.BOLD}\n!!! samplerate NOT configured, default to fs=44100\n{Fmt.END}')

    if not "plugins" in CONFIG or not CONFIG["plugins"]:
        CONFIG["plugins"] = []

    if not 'inputs' in CONFIG:
        CONFIG["inputs"] = {'system-wide':{}}
    else:
        CONFIG["inputs"]["none"] = {}

    if not 'drcs_offset' in CONFIG:
        CONFIG["drcs_offset"] = 0.0

    if not 'ref_level_gain_offset' in CONFIG:
        CONFIG["ref_level_gain_offset"] = 0.0

    if not "tones_span_dB" in CONFIG:
        CONFIG["tones_span_dB"] = 6.0


    # Converting the Human Readable outputs section to a dictionary
    reformat_outputs()

    # Converting the Human Readable PEQ section to a dictionary
    reformat_PEQ()


def wait4ports( pattern, timeout=10 ):
    """ Waits for jack ports with name *pattern* to be available.
        Default timeout 10 s
        (bool)
    """

    period = 0.25
    tries = int(timeout / period)

    while tries:
        tmp = sp.check_output(['jack_lsp', pattern]).decode().split()
        if len( tmp ) >= 2:
            break
        tries -= 1
        sleep(period)

    if tries:
        return True
    else:
        return False


def send_cmd( cmd, sender='', verbose=False, timeout=3,
              host='', port='' ):
    """
        Sends a command to a pAudio server partner.
        Returns a string about the execution response or an error if so.
    """
    if not host or not port:
        return 'bad address:port'

    if not sender:
        sender = 'share.common'

    # Default answer: "no answer from ...."
    ans = f'no answer from {host}:{port}'

    # (i) We prefer high-level socket function 'create_connection()',
    #     rather than low level 'settimeout() + connect()'
    try:

        with socket.create_connection( (host, port), timeout=timeout ) as s:

            s.send( cmd.encode() )

            if verbose:
                print( f'{Fmt.BLUE}(send_cmd) ({sender}) Tx: \'{cmd}\'{Fmt.END}' )

            ans = ''

            while True:

                tmp = s.recv(1024)

                if not tmp:
                    break

                ans += tmp.decode()

            if verbose:
                print( f'{Fmt.BLUE}(send_cmd) ({sender}) Rx: \'{ans}\'{Fmt.END}' )

            s.close()

    except Exception as e:

        ans = str(e)

        if verbose:
            print( f'{Fmt.RED}(send_cmd) ({sender}) {host}:{port} \'{ans}\' {Fmt.END}' )

    return ans


def get_DSP_in_use():
    """ The DSP in use is set inside preamp.py
    """
    with open(f'{CODEFOLDER}/services/preamp.py', 'r') as f:
        tmp = f.readlines()
    import_lines = [line for line in tmp if 'import ' in line]
    import_DSP_line = str([line for line in import_lines if 'DSP' in line])
    res = 'unknown'
    if 'camilla' in import_DSP_line:
        res = 'camilladsp'
    elif 'brutefir' in import_DSP_line:
        res = 'brutefir'
    return res


def get_bit_depth(fmt):
    """ retrieves the bit depth from a given audio sample format,
        e.g. FLOAT32LE, S24LE, ...
    """
    digits = [x for x in fmt if x.isdigit()]
    bd = ''.join(digits)
    return bd


def read_json_file(fpath, timeout=5):
    """ Some json files cannot be ready to read in first pAudio run,
        so let's retry
    """
    d = {}

    period = 0.5
    tries = int(timeout / period)
    while tries:
        try:
            with open(fpath, 'r') as f:
                d = json.loads(f.read())
            break
        except:
            tries -= 1
            sleep(period)

    if not tries:
        print(f'{Fmt.RED}(!) Cannot read `{fpath}`{Fmt.END}')

    if not d:
        print(f'{Fmt.RED}(i) Void JSON in `{fpath}`{Fmt.END}')

    return d


def save_json_file(d, fpath, timeout=1):
    """ Some json files cannot be ready to write because concurrency,
        so let's retry
    """

    period = 0.1
    tries = int(timeout / period)
    while tries:
        try:
            with open(fpath, 'w') as f:
                f.write(json.dumps(d))
            break
        except:
            tries -= 1
            sleep(period)

    if tries:
        return True
    else:
        return False


def read_yaml_file(fpath):
    with open(fpath, 'r') as f:
        c = yaml.safe_load(f.read())
    return c


def read_cmd_phrase(cmd_phrase):
    """
        Command phrase SYNTAX must start with an appropriate prefix:

            preamp  command  arg1 ... [add]
            players command  arg1 ...
            aux     command  arg1 ...

        The `add` option for relative level, bass, treble, ...

        The `preamp` prefix can be omited

        If not `command` will response the preamp state

    """

    pfx, cmd, argstring, add = '', '', '', False

    # This is to avoid empty values when there are more
    # than on space as delimiter inside the cmd_phrase:
    chunks = [x for x in cmd_phrase.split(' ') if x]

    if 'add' in chunks:
        add = True
        chunks.remove('add')

    if not chunks:
        chunks = ['preamp', 'state']

    # If not prefix, will treat as a preamp command kind of
    if not chunks[0] in ('preamp', 'player', 'aux'):
        chunks.insert(0, 'preamp')

    pfx = chunks[0]

    if chunks[1:]:
        cmd = chunks[1]

    if chunks[2:]:
        # <argstring> can be compound
        argstring = ' '.join( chunks[2:] )

    # Debug
    if False:
        print('pfx', pfx)
        print('cmd', cmd)
        print('arg', argstring)
        print('add', add)

    return pfx, cmd, argstring, add


def x2int(x):
    return int(round(float(x)))


def x2float(x):
    return round(float(x),1)


def x2bool(x):
    if x.lower() in ['true', 'on', '1']:
        return True
    elif x.lower() in ['false', 'off', '0']:
        return False
    else:
        return None


def switch(new, curr):
    if new == 'toggle':
        new = {True:False, False:True}[curr]
    else:
        new = x2bool(new)
    return new


def list_remove_by_pattern(l, p):
    l = [x for x in l if p not in x]
    return l


def get_xo_filters_from_loudspeaker_folder():
    """ looks for xo.xxxx.pcm files inside the loudspeaker folder
    """
    xo_files    = []
    xo_filters  = []

    LSPKFOLDER_FS = f'{LSPKFOLDER}/{CONFIG["samplerate"]}'

    try:
        files = os.listdir(LSPKFOLDER_FS)
        files = [x for x in files if os.path.isfile(f'{LSPKFOLDER_FS}/{x}') ]
        xo_files = [x for x in files if x.startswith('xo.')
                                        and
                                        x.endswith('.pcm')]
    except Exception as e:
        print(f'{Fmt.BOLD}get_xo_filters_from_loudspeaker_folder ERROR: {str(e)}{Fmt.END}')

    for f in xo_files:
        xo_id = f.replace('xo.', '').replace('.pcm', '')
        xo_filters.append(xo_id)

    return xo_filters


def get_xo_sets_from_loudspeaker_folder():
    """ xo.WW.FF.pcm files can exist on two flavours:

            FF = mp: minimum phase filter
            FF = lp: linear phase filter
    """
    xo_filters = get_xo_filters_from_loudspeaker_folder()

    xo_sets = [ x.replace('lo.', '')
                 .replace('mi.', '')
                 .replace('hi.', '')
                 .replace('sw.', '') for x in xo_filters ]

    return list(set(xo_sets))


def get_loudspeaker_ways():
    """ Read loudspeaker ways as per the outputs configuration
    """
    lws = []
    for o, pms in CONFIG["outputs"].items():
        if not 'sw' in pms["name"]:
            w = pms["name"].replace('.L', '').replace('.R', '')
            lws.append(w)
        else:
            lws.append('sw')
    return list(set(lws))


def get_drc_sets_from_loudspeaker_folder():
    """ looks for drc.Channel.DrcId.pcm files inside the loudspeaker folder
    """
    drc_files = []
    drc_sets_candidate  = {}
    drc_sets = []

    try:
        files = os.listdir(f'{LSPKFOLDER}')
        files = [x for x in files if os.path.isfile(f'{LSPKFOLDER}/{x}') ]
        drc_files = [x for x in files if x.startswith('drc.') ]
    except:
        pass

    for f in drc_files:
        chID  = f.split('.')[1]
        drcID = '.'.join(f.split('.')[2:]).replace('.pcm', '')
        if not drcID in drc_sets_candidate:
            drc_sets_candidate[drcID] = [chID]
        else:
            if not chID in drc_sets_candidate[drcID]:
                drc_sets_candidate[drcID].append(chID)

    for k in drc_sets_candidate:
        channels = drc_sets_candidate[k]
        if sorted(channels) == ['L', 'R']:
            drc_sets.append(k)

    return sorted(drc_sets)


def get_target_sets(fs=44100):
    """ looks for '+x.x-x.x_target_mag.dat files inside the eq folder
    """
    targets_folder  = f'{EQFOLDER}/curves_{fs}_N11/room_target'
    files = []
    sets  = []

    try:
        files = os.listdir(targets_folder)
        files = [x for x in files if os.path.isfile(f'{targets_folder}/{x}') ]
        files = [x for x in files if x.endswith('_target_mag.dat') ]
    except:
        pass

    for file in files:
        tID = file.split('_target')[0]
        if not tID in sets:
            sets.append(tID)

    return sorted(sets)


def run_plugins(mode='start'):
    """ Run plugins (stand-alone processes)
    """

    if not 'plugins' in CONFIG or not CONFIG["plugins"]:
        return

    if mode == 'start':
        for plugin in CONFIG["plugins"]:
            print(f'{Fmt.MAGENTA}Runinng plugin: {plugin} ...{Fmt.END}')
            sp.Popen(f'{PLUGINSFOLDER}/{plugin} start', shell=True)

    elif mode == 'stop':
        for plugin in CONFIG["plugins"]:
            print(f'{Fmt.BLUE}Stopping plugin: {plugin} ...{Fmt.END}')
            sp.Popen(f'{PLUGINSFOLDER}/{plugin} stop', shell=True)


def process_is_running(pattern):
    """ check for a system process to be running by a given pattern
        (bool)
    """
    try:
        # do NOT use shell=True because pgrep ...  will appear it self.
        plist = sp.check_output(['pgrep', '-fla', pattern]).decode().split('\n')
    except:
        return False
    for p in plist:
        if pattern in p:
            return True
    return False


def wait4server(timeout=60):

    period = .5
    tries  = int(timeout / period)

    while tries:
        try:
            sp.check_output('echo aux hello | nc localhost 9980', shell=True)
            break
        except:
            tries -= 1
            sleep(period)

    if tries:
        return True
    else:
        return False


def wait4jackports( pattern, timeout=5 ):
    """ Waits for jack ports with name *pattern* to be available.
        Returns: <bool>
    """
    period = .25
    tries = int(timeout / period)

    while tries:
        try:
            tmp = sp.check_output(f'jack_lsp {pattern} 2>/dev/null', shell=True).decode().split()
        except:
            tmp = []
        if len( tmp ) >= 2:
            break
        tries -= 1
        sleep(period)

    if tries:
        return True
    else:
        return False


def get_default_device_PENDING():
    #
    #  PENDING:
    #    system_profiler does not reflects the real one ¿!?
    #

    def find_dd(audio_profile):
        dd = ''
        for item in audio_profile["SPAudioDataType"][0]["_items"]:
            if 'coreaudio_default_audio_system_device' in item and \
               item["coreaudio_default_audio_system_device"] == 'spaudio_yes' and \
               'coreaudio_output_source' in item and \
               item["coreaudio_output_source"] == 'spaudio_default':
                   dd = item["_name"]
        return dd


    if  not CONFIG.get('coreaudio'):
        return ''

    dd = ''

    cmd = 'system_profiler -json $( system_profiler -listDataTypes | grep Audio)'
    try:
        tmp = sp.check_output(cmd, shell=True).decode().strip()
        audio_profile = json.loads(tmp)
        dd = find_dd(audio_profile)
    except:
        pass

    return dd


def get_default_device():
    """ Currently only works with CoreAudio
        AND NEEDS SwitchAudioSource
    """
    if  not CONFIG.get('coreaudio'):
        return ''

    dd = ''
    try:
        dd = sp.check_output('SwitchAudioSource -c'.split()).decode().strip()
    except Exception as e:
        print(f'(pAudio) warning: {str(e)}')
    return dd


def get_default_device_vol():
    """ Currently only works with CoreAudio
    """
    if  not CONFIG.get('coreaudio'):
        return ''

    cmd = "osascript -e 'output volume of (get volume settings)'"
    try:
        vol = sp.check_output(cmd, shell=True).decode().strip()
    except Exception as e:
        print(f'(pAudio) warning: {str(e)}')
        vol = ''
    return vol


def set_default_device_vol(vol):
    """ Currently only works with CoreAudio
    """
    if  not CONFIG.get('coreaudio'):
        return 'not available'

    dev = get_default_device()

    cmd = f'osascript -e "set volume output volume {vol}"'

    tmp = sp.call(cmd, shell=True)

    if tmp == 0:
        print(f'{Fmt.BOLD}{Fmt.BLUE}Setting VOLUME to MAX on "{dev}"{Fmt.END}')
        return 'done'

    else:
        print(f'(pAudio) Problems setting system volume to MAX on "{dev}"')
        return 'error'


def set_device_vol(dev, vol):
    """ Based on `AdjustVolume` from
        https://github.com/jonomuller/device-volume-adjuster
    """

    try:
        vol_unit = round( int(vol) / 100, 3)
        cmd = f'AdjustVolume -s {vol_unit} -n "{dev}"'
        sp.call(cmd, shell=True)
        print(f'{Fmt.BOLD}{Fmt.BLUE}Setting VOLUME to {vol} on "{dev}"{Fmt.END}')
        return 'done'

    except Exception as e:
        print(f'(pAudio) ERROR with AdjustVolume: {str(e)}')
        return 'error'


def set_default_device_mute(mode='false'):
    """ Currently only works with CoreAudio
    """
    if  not CONFIG.get('coreaudio'):
        return 'not available'

    dev = get_default_device()

    cmd = f'osascript -e "set volume output muted {mode}"'

    tmp = sp.call(cmd, shell=True)

    if tmp == 0:
        if mode == 'true':
            print(f'{Fmt.BOLD}{Fmt.BLUE}Mutting "{dev}"{Fmt.END}')
        else:
            print(f'{Fmt.BOLD}{Fmt.BLUE}Un-mutting"{dev}"{Fmt.END}')
        return 'done'

    else:
        print(f'(pAudio) Problems muting on "{dev}"')
        return 'error'


def save_default_sound_device():
    """ Save the current system-wide sound device
        ONLY for CoreAudio
    """

    cur_dd = get_default_device()
    if cur_dd:
        print(f'{Fmt.BLUE}Saving current Playback Device: "{cur_dd}"{Fmt.END}')
        with open(f'{MAINFOLDER}/.previous_default_device', 'w') as f:
            f.write(cur_dd)
    else:
        print(f'{Fmt.RED}ERROR getting the current Playback Device.{Fmt.END}')


    cur_dd_vol = get_default_device_vol()
    if cur_dd_vol:
        print(f'{Fmt.BLUE}Saving current Playback Volume: "{cur_dd_vol}"{Fmt.END}')
        with open(f'{MAINFOLDER}/.previous_default_device_volume', 'w') as f:
            f.write(cur_dd_vol)
    else:
        print(f'{Fmt.RED}ERROR getting the current Playback Volume.{Fmt.END}')


def change_default_sound_device(new_dev):
    """
        - Change default system-wide sound device
        - Set max volume to device

        Currently only works with CoreAudio
    """

    if  not CONFIG.get('coreaudio'):
        return

    # Getting PREVIOUS PLAYBACK DEV
    old_dev = get_default_device()

    # SWITCHING PLAYBACK DEV ---> CamillaDSP_capture
    cmd_source = f'SwitchAudioSource -s \"{new_dev}\"'
    tmp = sp.call(cmd_source, shell=True)
    if tmp == 0:
        print(f'{Fmt.BOLD}{Fmt.BLUE}Setting MacOS Playback Default Device: "{new_dev}"{Fmt.END}')
    else:
        print(f'(pAudio) Problems setting default MacOS playback default device')

    # Set volume to max on the NEW PLAYBACK DEV
    set_default_device_vol('100')

    # Set volume to max on the PREVIOUS PLAYBACK DEV
    set_device_vol(old_dev, '100')


def restore_playback_device_settings():
    """ Only for MacOS CoreAudio """

    if sys.platform == 'darwin':

        # Restore dsefault device
        try:
            with open(f'{MAINFOLDER}/.previous_default_device', 'r') as f:
                dev = f.read().strip()
        except:
            dev = ''

        if dev:
            print("(start.py) Restoring previous Default Playback Device")
            sp.call(f'SwitchAudioSource -s "{dev}"', shell=True)
        else:
            print("(start.py) Cannot read `.previous_default_device`")

        # Restore volume
        try:
            with open(f'{MAINFOLDER}/.previous_default_device_volume', 'r') as f:
                vol = f.read().strip()
        except:
            vol = ''

        if vol:
            print("(start.py) Restoring previous Playback Device Volume")
            sp.call(f"osascript -e 'set volume output volume '{vol}", shell=True)
        else:
            print("(start.py) Cannot read `.previous_default_device_volume`")


def is_IP(s):
    """ Validate if a given string is a valid IP address
        (bool)
    """
    if type(s) == str:
         try:
             ipaddress.ip_address(s)
             return True
         except:
             return False
    else:
         return False


def get_my_ip():
    """ retrieves the own IP address
        (string)
    """
    try:
        tmp = sp.check_output( 'hostname --all-ip-addresses'.split() ).decode()
        return tmp.split()[0]
    except:
        return ''


def remote_zita_restart(raddr='', ctrl_port=0, zita_port=0, mode='restart'):
    """
        Restarting zita-j2n on the multiroom sender's end,
        pointing to our ip.

        (i) The sender will run zita_j2n only when a receiver request it
    """

    if mode == 'stop':

        zargs = json.dumps( (get_my_ip(), None, 'stop') )
        remotecmd = f'aux zita_j2n {zargs}'

        print(f'{Fmt.GRAY}(common) stopping remote {raddr}: {remotecmd}{Fmt.END}')

        send_cmd(remotecmd, host=raddr, port=ctrl_port, timeout=1)

        return None


    zargs     = json.dumps( (get_my_ip(), zita_port, 'start') )
    remotecmd = f'aux zita_j2n {zargs}'
    result = send_cmd(remotecmd, host=raddr, port=ctrl_port)

    print(f'(common) SENDING TO REMOTE: {remotecmd}')

    return result


def local_zita_restart(raddr='', udp_port=0, buff_size=20, jport='', mode='restart'):
    """
        Run zita-n2j listen ports on the multiroom receiver's end.

        (i) Will log zita process printouts under LOGFOLDER
    """

    if mode == 'stop':

        print(f'{Fmt.GRAY}(common) killing local zita-n2j: {jport}{Fmt.END}')

        zitapattern  = f'zita-n2j --jname {jport}'
        sp.call( ['pkill', '-KILL', '-u', USER, '-f',  zitapattern] )

        return None


    zitajname = f'zita_n2j_{ raddr.split(".")[-1] }'
    zitacmd   = f'zita-n2j --jname {zitajname} --buff {buff_size} {get_my_ip()} {udp_port}'

    # Assign ALIAS to ports to be able to switch by using
    # the IP port name of a remoteXXXX input in config.yml
    #
    with open(f'{LOGFOLDER}/{zitajname}.log', 'w') as zitalog:

        # Ignore if zita-njbridge is not available
        try:
            sp.Popen( zitacmd.split(), stdout=zitalog, stderr=zitalog )
            wait4ports(zitajname, 3)
            sp.Popen( f'jack_alias {zitajname}:out_1 {raddr}:out_1'.split() )
            sp.Popen( f'jack_alias {zitajname}:out_2 {raddr}:out_2'.split() )
            print(f'(common) RUNNING LOCAL: {zitacmd}, LOGGING under {LOGFOLDER}')

        except Exception as e:
            print(f'(common) ERROR: {e}, you may want run it for a remote source?')


init()
