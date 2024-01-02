#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  subprocess as sp
import  threading
from    time import sleep
import  yaml
import  json
from    fmt import Fmt
import  sys
import  os

UHOME = os.path.expanduser('~')

MAINFOLDER          = f'{UHOME}/paudio'
LSPKSFOLDER         = f'{MAINFOLDER}/loudspeakers'
LSPKFOLDER          = f''
LOUDSPEAKER         = f''   # to be found when loading CONFIG
EQFOLDER            = f'{MAINFOLDER}/eq'
CODEFOLDER          = f'{MAINFOLDER}/code'
CONFIG_PATH         = f'{MAINFOLDER}/config.yml'
DSP_LOGFOLDER       = f'{MAINFOLDER}/log'
PLUGINSFOLDER       = f'{MAINFOLDER}/code/share/plugins'

LDCTRL_PATH         = f'{MAINFOLDER}/.loudness_control'
LDMON_PATH          = f'{MAINFOLDER}/.loudness_monitor'
AUXINFO_PATH        = f'{MAINFOLDER}/.aux_info'
PLAYER_META_PATH    = f'{MAINFOLDER}/.player_metadata'


try:
    os.mkdir(DSP_LOGFOLDER)
except:
    pass

CONFIG = {}


def init():


    def reformat_outputs():
        """
            Outputs are given in NON standard YML, having 4 fields.

            An output can be void, or at least must have a valid name:

                Out:    Name   Gain    Polarity  Delay(ms)

            Will convert the Human Readable fields into a dictionary.
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


        # Outputs
        void_count = 0
        for out, params in CONFIG["outputs"].items():

            # It is expected 4 fields
            params = params.split() if params else []
            params += [''] * (4 - len(params))

            # Redo in dictionary form
            if not any(params):
                void_count += 1
                params = {'name': f'void_{void_count}', 'gain': 0.0,
                          'polarity': '', 'delay': 0.0}

            else:
                _, p = check_output_params(out, params)
                name, gain, pol, delay = p
                params = {'name': name, 'gain': gain, 'polarity': pol, 'delay': delay}

            CONFIG["outputs"][out] = params


        # Number of outputs must match the sound card
        # TO BE DONE


    global CONFIG, LOUDSPEAKER, LSPKFOLDER

    CONFIG = read_yaml_file(CONFIG_PATH)

    try:
        LSPKFOLDER = f'{LSPKSFOLDER}/{CONFIG["loudspeaker"]}'
        if not os.path.isdir(LSPKFOLDER):
            print(f'ERROR with LOUDSPEAKER FOLDER configuration')
            sys.exit()
    except Exception as e:
        print(f'ERROR with LOUDSPEAKER configuration')
        sys.exit()

    LOUDSPEAKER = CONFIG["loudspeaker"]

    CONFIG["DSP"] = get_DSP_in_use()

    if not "fs" in CONFIG:
        CONFIG["fs"] = 44100
        print(f'{Fmt.BOLD}\n!!! fs NOT configured, default to fs=44100\n{Fmt.END}')

    if not "plugins" in CONFIG or not CONFIG["plugins"]:
        CONFIG["plugins"] = []

    # Converting the Human Readable outputs section to a dictionary
    reformat_outputs()


def get_lspk_ways():
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


def read_json_file(fpath):
    with open(fpath, 'r') as f:
        d = json.loads(f.read())
    return d


def save_json_file(d, fpath):
    c=10
    while c:
        try:
            with open(fpath, 'w') as f:
                f.write(json.dumps(d))
            break
        except:
            sleep (.1)
            c -= 1
    if c:
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

        The 'preamp' prefix can be omited

        The 'add' option for relative level, bass, treble, ...
    """

    pfx, cmd, argstring, add = '', '', '', False

    # This is to avoid empty values when there are more
    # than on space as delimiter inside the cmd_phrase:
    chunks = [x for x in cmd_phrase.split(' ') if x]

    if 'add' in chunks:
        add = True
        chunks.remove('add')

    # If not prefix, will treat as a preamp command kind of
    if not chunks[0] in ('preamp', 'player', 'aux'):
        chunks.insert(0, 'preamp')
    pfx = chunks[0]

    if chunks[1:]:
        cmd = chunks[1]
    if chunks[2:]:
        # <argstring> can be compound
        argstring = ' '.join( chunks[2:] )

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


def get_xo_sets_from_loudspeaker_folder():
    """ looks for xo.xxxx.pcm files inside the loudspeaker folder
    """
    xo_files = []
    xo_sets  = []

    try:
        files = os.listdir(f'{LSPKFOLDER}')
        files = [x for x in files if os.path.isfile(f'{LSPKFOLDER}/{x}') ]
        xo_files = [x for x in files if x.startswith('xo.')
                                        and
                                        x.endswith('.pcm')]
    except:
        pass

    for f in xo_files:
        xo_id = f.replace('xo.', '').replace('.pcm', '')
        xo_sets.append(xo_id)

    return xo_sets


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


    if  CONFIG["sound_server"].lower() != "coreaudio":
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
    if  CONFIG["sound_server"].lower() != "coreaudio":
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
    if  CONFIG["sound_server"].lower() != "coreaudio":
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
    if  CONFIG["sound_server"].lower() != "coreaudio":
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
    if  CONFIG["sound_server"].lower() != "coreaudio":
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
    """

    cur_dd = get_default_device()
    if cur_dd:
        print(f'{Fmt.BLUE}Saving current Playback Device: "{cur_dd}"{Fmt.END}')
        with open(f'{MAINFOLDER}/.previous_default_device', 'w') as f:
            f.write(cur_dd)
    else:
        print(f'{Fmt.RED} ERROR getting the current Playback Device.{Fmt.END}')


    cur_dd_vol = get_default_device_vol()
    if cur_dd_vol:
        print(f'{Fmt.BLUE}Saving current Playback Volume: "{cur_dd_vol}"{Fmt.END}')
        with open(f'{MAINFOLDER}/.previous_default_device_volume', 'w') as f:
            f.write(cur_dd_vol)
    else:
        print(f'{Fmt.RED} ERROR getting the current Playback Volume.{Fmt.END}')


def change_default_sound_device(new_dev):
    """
        - Change default system-wide sound device
        - Set max volume to device

        Currently only works with CoreAudio
    """

    if  CONFIG["sound_server"].lower() != "coreaudio":
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


init()
