#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  os
import  subprocess as sp
import  math

UHOME = os.path.expanduser('~')


class Fmt:
    GREEN           = '\033[32m'
    BLUE            = '\033[34m'
    MAGENTA         = '\033[35m'
    CYAN            = '\033[36m'
    GRAY            = '\033[90m'
    BOLD            = '\033[1m'
    END             = '\033[0m'


def init():

    global SWITCHAUDIO_BIN, ADJUSTVOLUME_BIN

    BREW                = '/opt/homebrew'
    LOCAL               = 'usr/local'
    SWITCHAUDIO_BIN     = ''
    ADJUSTVOLUME_BIN    = ''

    if os.path.isfile(f'{UHOME}/bin/SwitchAudioSource'):
        SWITCHAUDIO_BIN = f'{UHOME}/bin/SwitchAudioSource'
    else:
        if os.path.isfile(f'{BREW}/bin/SwitchAudioSource'):
            SWITCHAUDIO_BIN = f'{BREW}/bin/SwitchAudioSource'
        else:
            if os.path.isfile('/usr/local/bin/SwitchAudioSource'):
                SWITCHAUDIO_BIN = '/usr/local/bin/SwitchAudioSource'


    if os.path.isfile(f'{UHOME}/bin/AdjustVolume'):
        ADJUSTVOLUME_BIN = f'{UHOME}/bin/AdjustVolume'
    else:
        if os.path.isfile(f'{LOCAL}/bin/AdjustVolume'):
            ADJUSTVOLUME_BIN = f'{LOCAL}/bin/AdjustVolume'

    if SWITCHAUDIO_BIN:
        print(f'{Fmt.GREEN}(macos) SwitchAudioSource tool detected{Fmt.END}')
    else:
        print(f'{Fmt.GRAY}(macos) SwitchAudioSource NOT available{Fmt.END}')

    if ADJUSTVOLUME_BIN:
        print(f'{Fmt.GREEN}(macos) AdjustVolume tool detected{Fmt.END}')
    else:
        print(f'{Fmt.GRAY}(macos) AdjustVolume NOT available{Fmt.END}')


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


def get_current_device():
    """ (needs SwitchAudioSource)
    """
    if  not CONFIG.get('coreaudio'):
        return ''

    dd = ''

    if SWITCHAUDIO_BIN:
        try:
            dd = sp.check_output(f'{SWITCHAUDIO_BIN} -c'.split()).decode().strip()
        except Exception as e:
            print(f'{Fmt.GRAY}(macos) warning: {str(e)}{Fmt.END}')

    return dd


def get_default_device_vol():

    if  not CONFIG.get('coreaudio'):
        return ''

    cmd = "osascript -e 'output volume of (get volume settings)'"
    try:
        vol = sp.check_output(cmd, shell=True).decode().strip()
    except Exception as e:
        print(f'{Fmt.GRAY}(macos) warning: {str(e)}{Fmt.END}')
        vol = ''
    return vol


def set_default_device_vol(vol):

    if  not CONFIG.get('coreaudio'):
        return 'not available'

    dev = get_current_device()

    cmd = f'osascript -e "set volume output volume {vol}"'

    tmp = sp.call(cmd, shell=True)

    if tmp == 0:
        print(f'{Fmt.BOLD}{Fmt.BLUE}Setting VOLUME to MAX on "{dev}"{Fmt.END}')
        return 'done'

    else:
        print(f'{Fmt.GRAY}(macos) Problems setting system volume to MAX on "{dev}"{Fmt.END}')
        return 'error'


def set_device_vol(dev, vol):
    """ Based on `AdjustVolume` from
        https://github.com/jonomuller/device-volume-adjuster
    """

    if ADJUSTVOLUME_BIN:

        try:
            vol_unit = round( int(vol) / 100, 3)
            cmd = f'{ADJUSTVOLUME_BIN} -s {vol_unit} -n "{dev}"'
            sp.call(cmd, shell=True)
            print(f'{Fmt.BOLD}{Fmt.BLUE}Setting VOLUME to {vol} on "{dev}"{Fmt.END}')
            return 'done'

        except Exception as e:
            print(f'{Fmt.GRAY}(macos) ERROR with AdjustVolume: {str(e)}{Fmt.END}')
            return 'error with AdjustVolume'

    else:
        return 'error AdjustVolume not available'


def set_default_device_mute(mode='false'):

    if  not CONFIG.get('coreaudio'):
        return 'not available'

    dev = get_current_device()

    cmd = f'osascript -e "set volume output muted {mode}"'

    tmp = sp.call(cmd, shell=True)

    if tmp == 0:
        if mode == 'true':
            print(f'{Fmt.BOLD}{Fmt.BLUE}Mutting "{dev}"{Fmt.END}')
        else:
            print(f'{Fmt.BOLD}{Fmt.BLUE}Un-mutting"{dev}"{Fmt.END}')
        return 'done'

    else:
        print(f'{Fmt.GRAY}(macos) Problems muting on "{dev}"{Fmt.END}')
        return 'error'


def save_default_sound_device():
    """ Save the current system-wide sound device
    """

    cur_dd = get_current_device()

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
    """

    if  not CONFIG.get('coreaudio'):
        return

    # Getting PREVIOUS PLAYBACK DEV
    old_dev = get_current_device()

    # SWITCHING PLAYBACK DEV ---> CamillaDSP_capture
    if SWITCHAUDIO_BIN:
        cmd_source = f'{SWITCHAUDIO_BIN} -s \"{new_dev}\"'
        tmp = sp.call(cmd_source, shell=True)
        if tmp == 0:
            print(f'{Fmt.BOLD}{Fmt.BLUE}Setting macOS Playback Default Device: "{new_dev}"{Fmt.END}')
        else:
            print(f'{Fmt.GRAY}(macos) Problems setting default macOS playback default device{Fmt.END}')

    # Set volume to max on the NEW PLAYBACK DEV
    set_default_device_vol('100')

    # Set volume to max on the PREVIOUS PLAYBACK DEV
    set_device_vol(old_dev, '100')


def set_playback_device_volume(volume_dB = -20):
    """
        Audio MIDI

        Value    dB
        0.0     -63.5
        0.01    -57.15
        0.02    -54.52
        0.03    -52.5
        0.04    -50.8
        0.05    -49.3
        0.06    -47.95
        0.07    -46.7
        0.08    -45.54
        0.09    -44.45
        0.10    -43.42
        0.15    -38.91
        0.20    -35.1
        0.25    -31.75
        0.30    -28.72
        0.35    -25.93
        0.40    -23.34
        0.45    -20.9
        0.50    -18.6
        0.55    -16.41
        0.60    -14.31
        0.65    -12.3
        0.70    -10.37
        0.75    -8.51
        0.80    -6.7
        0.85    -4.96
        0.90    -3.26
        0.95    -1.61
        1.00    0.0

        dB = -63.5 * (1 - sqrt(Value))

        Value = (1 + dB / 63.5) ** 2

    """

    volume_percent  = (1 + volume_dB / 63.5) ** 2 * 100
    dev             = ''

    try:
        cmd = """system_profiler SPAudioDataType \
               | awk '/:$/ {device=$0} /Default System Output Device: Yes/ {print device}' \
               | sed 's/^[ \t]*//;s/://'
        """
        dev = sp.check_output(cmd, shell=True).decode().strip()

    except Exception as e:
        print(f'{Fmt.RED}(set_playback_device_volume) ERROR getting Default System Output Device: {e}{Fmt.END}')

    if dev:
        if SWITCHAUDIO_BIN:
            sp.call(f'{SWITCHAUDIO_BIN} -s "{dev}"', shell=True)
            sp.call(f"osascript -e 'set volume output volume '{volume_percent}", shell=True)
            print(f'{Fmt.BLUE}(set_playback_device_volume) Restoring Playback Device volume to {volume_dB} dB{Fmt.END}')

        else:
            print(f'{Fmt.RED}(set_playback_device_volume) SwitchAudioSource NOT AVAILABLE{Fmt.END}')

    else:
            print(f'{Fmt.RED}(set_playback_device_volume) UNABLE to find default system output device{Fmt.END}')


init()
