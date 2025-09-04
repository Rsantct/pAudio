#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  subprocess as sp
import  psutil
import  threading
import  socket
from    time        import sleep, strftime
from    datetime    import datetime
import  yaml
import  json
import  shlex
from    fmt         import Fmt
import  sys
import  ipaddress
from    getpass     import getuser
from    config      import *

USER = getuser()

METATEMPLATE = {
    'player':       '',
    'state':        '',
    'time_pos':     '',
    'time_tot':     '',
    'bitrate':      '',
    'artist':       '',
    'album':        '',
    'title':        '',
    'track_num':    '',
    'track_uri':    '',
    'tracks_tot':   ''
}


def read_mpd_config(mpd_config_path=''):
    """ mpd clients CANNOT access to MPD.config(),
        so them needs to rely in reading the mpd config file

        If no `mpd_config_path` is given, then will look for
        the one used by the running MPD process.
    """

    def get_running_mpd_config_path():

        result = f'{UHOME}/.mpdconf'

        # Example: [{'pid': 12430, 'cmdline': ['mpd', '/home/paudio/.mpdconf.local']}]
        mpd_processes = get_pid_cmdline('mpd')

        # If more tan one, raise an Exception
        if len(mpd_processes) > 1:

            msg = 'More than ONE `mpd` process is running'
            print(f'{Fmt.BOLD}(mpd_mod) {msg}{Fmt.END}')
            raise Exception(msg)

        elif len(mpd_processes) == 1:

            # mpd [options] [conf_file]: it is always the last parameter
            if len( mpd_processes[0]['cmdline'] ) > 1:
                result = mpd_processes[0]['cmdline'][-1]

        else:
            msg = 'mpd process NOT detected'
            print(f'{Fmt.RED}(mpd_mod) {msg}{Fmt.END}')

        return result


    def strip(x):
        """ removes " for config values
        """

        if type(x) != str:
            return x

        if x[0] == '"' and x[-1] == '"':
            return x[1:-1]


    config = {'port': 6600, 'playlist_directory': f'{UHOME}/.config/mpd/playlists'}


    if not mpd_config_path:
        mpd_config_path = get_running_mpd_config_path()


    with open(mpd_config_path, 'r') as f:

        lexer = shlex.shlex(f)
        lexer.wordchars += ".-/" # Important for file paths etc.

        section = None

        while True:

            try:
                token = lexer.get_token()
                if not token:
                    break  # End of file
                if token == '{':
                    continue
                if token == '}':
                    section = None
                    continue
                next_token = lexer.get_token()
                if next_token == '{':
                    section = token
                    config.setdefault(section, {})
                    continue
                if next_token:
                    if next_token.lower() in ("yes", "true", "1"):
                        next_token = True
                    elif next_token.lower() in ("no", "false", "0"):
                        next_token = False
                    if section:
                        config[section][token] = strip(next_token)
                    else:
                        config[token] = strip(next_token)

            except ValueError:
                print(f"Error parsing line {lexer.lineno}: {lexer.error_leader()}")
                return {}

            except EOFError: # shlex sometimes raises EOFError
                break

    return config


def player_from_source():

    source = read_json_file(PREAMP_STATE_PATH).get('source', 'none')
    lowsource = source.lower()

    if lowsource == 'spotify':
        player = 'spotify'

    elif 'mpd' in lowsource or lowsource == 'cd':
        player = 'mpd'

    elif 'tdt' in lowsource or 'dvb' in lowsource:
        player = 'mplayer'

    elif source[:6] == 'remote':
        player = source

    else:
        player = ''

    return player


def get_web_config():

    # LU_monitor_enabled is a legacy option, now it is always enabled.

    result = {  'main_selector':        'sources',
                'LU_monitor_enabled':   True,
                'onoff':                'pAudio',
                'monkey_button':        'toggle'
    }

    for item, value in CONFIG.get('web_config', {}).items():
        result[item] = value

    return result


def amp_switch(mode):

    def read_amp_state_file():

        try:
            with open(AMP_STATE_PATH, 'r') as f:
                tmp = f.read().strip()

                if tmp.lower() in ('on', '1'):
                    return 'on'
                elif tmp.lower() in ('off', '0'):
                    return 'off'
                else:
                    print(f'{Fmt.MAGENTA}(common.amp_switch) amp file weird state value: {tmp}{Fmt.END}' )
                    return tmp

        except Exception as e:
            print(f'{Fmt.MAGENTA}(common.amp_switch) error reading amp state file: {str(e)}{Fmt.END}' )
            return '--'


    def get_state():
        """
            (i) NOT IN USE  -->  read_amp_state_file()
        """

        return read_amp_state_file()

        try:
            res = sp.check_output(AMP_CMD, shell=True).decode().strip().lower()

        except Exception as e:
            print(f'(common.amp_switch) get_state ERROR: {str(e)}')

        if res in (1, '1', 'on'):
            res = 'on'
        else:
            res = 'off'

        return res


    def set_state(new):
        """
            $ ampli.sh 1
            BITFT_1=0
            BITFT_2=0
            1
        """

        if new == None:
            return 'must be: on | off'

        if new:

            try:
                res = sp.check_output(f'{AMP_CMD} {new}', shell=True).decode().strip().lower()
                # (**) see docstring
                res = res.strip().split()[-1]

            except Exception as e:
                print(f'(common.amp_switch) set_state ERROR: {str(e)}')

        if res in (1, '1', 'on'):
            res = 'on'
        else:
            res = 'off'

        return res


    AMP_CMD = CONFIG.get('amplifier_switch_cmd', '~/bin/ampli.sh')

    res = 'NAK'

    if not mode:
        mode = 'state'

    match mode:

        case 'state':
            res = read_amp_state_file()

        case 'on':
            res = set_state('on')

        case 'off':
            res = set_state('off')

        case 'toggle':
            curr = get_state()
            new = {'on':'off', 'off':'on'}[curr]
            res = set_state(new)

        case _:
            pass

    return res


def restore_sound_card():
    """
        This assumes that you have set your alsamixer levels and saved them to:
            ~/pAudio/alsactl.<YOUR_ALSA_CARD_NAME>
    """

    pa_config_path = f'{UHOME}/pAudio/config.yml'

    with open(pa_config_path, 'r') as f:
        pa_config = yaml.safe_load( f.read() )

    if not pa_config.get('jack'):
        return

    alsa_device = pa_config["jack"]["device"]
    # example: hw:UDJ6,0

    alsa_name = alsa_device.split(',')[0].split(':')[-1]

    alsactl_path =  f'{UHOME}/pAudio/alsactl.{alsa_name}'

    cmd = f'alsactl --file {alsactl_path} restore {alsa_name}'

    if os.path.isfile(alsactl_path):
        print(f'{Fmt.BLUE}Restoring: {alsactl_path}{Fmt.END}')
        sp.call(cmd, shell=True)

    else:
        print(f'{Fmt.RED}File not found: {alsactl_path}{Fmt.END}')


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


def send_cmd( cmd, sender='', verbose=False, timeout=3, host=PAUDIO_ADDR, port=PAUDIO_PORT ):
    """ Sends a command to a pAudio server partner.
        Returns a string about the execution response or an error if so.
    """

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


def read_state_from_disk():
    """ wrapper for reading the state dict
        (dictionary)
    """
    return read_json_file(PREAMP_STATE_PATH)


def read_metadata_from_disk():
    """ wrapper for reading the playing metadata dict
        (dictionary)
    """
    return read_json_file(PLAYER_META_PATH)


def read_cdda_meta_from_disk():
    """ wrapper for reading the cdda metadata dict from disk
        (dictionary)
    """

    result = read_json_file( CDDA_META_PATH )

    if not result:
        result = CDDA_META_TEMPLATE.copy()

    return result


def read_json_file(fpath, timeout=1, quiet=False):
    """ Some json files cannot be ready to read in first pAudio run,
        so let's retry
    """
    d = {}

    period = 0.25
    tries = int(timeout / period)
    while tries:

        try:
            with open(fpath, 'r') as f:
                d = json.loads(f.read())
            break

        except:
            tries -= 1
            sleep(period)

    if not quiet:
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


def read_last_line(filename=''):
    """ Read the last line from a large file, efficiently.
        (string)
    """
    # credits:
    # https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python
    # For large files it would be more efficient to seek to the end of the file,
    # and move backwards to find a newline.
    # Note that the file has to be opened in binary mode, otherwise,
    # it will be impossible to seek from the end.
    #
    # https://python-reference.readthedocs.io/en/latest/docs/file/seek.html
    # f.seek( offset, whence )

    if not filename:
        return ''

    try:
        with open(filename, 'rb') as f:
            f.seek(-2, os.SEEK_END)             # Go to -2 bytes from file end

            while f.read(1) != b'\n':           # Repeat reading until find \n
                f.seek(-2, os.SEEK_CUR)

            last_line = f.readline().decode()   # readline reads until \n

        return last_line.strip()

    except:
        return ''


def read_last_lines(filename='', nlines=1):
    """ Read the last N lines from a large file, efficiently.
        (list of strings)
    """
    # credits:
    # https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python
    # For large files it would be more efficient to seek to the end of the file,
    # and move backwards to find a newline.
    # Note that the file has to be opened in binary mode, otherwise,
    # it will be impossible to seek from the end.
    #
    # https://python-reference.readthedocs.io/en/latest/docs/file/seek.html
    # f.seek( offset, whence )

    if not filename:
        return ['']

    try:
        with open(filename, 'rb') as f:
            f.seek(-2, os.SEEK_END)

            c = nlines
            while c:
                if f.read(1) == b'\n':
                    c -= 1
                f.seek(-2, os.SEEK_CUR)

            lines = f.read().decode()[2:].replace('\r', '').split('\n')

        return [x.strip() for x in lines if x]

    except:
        return ['']


def read_cmd_phrase(cmd_phrase):
    """
        Command phrase SYNTAX must start with an appropriate prefix:

            preamp  command  arg1 ... [add]
            player  command  arg1 ...

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
    if not chunks[0] in ('preamp', 'player', 'ctrl'):
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

    if type(x) == str:

        if x.lower() in ['true', 'on', '1']:
            return True

        elif x.lower() in ['false', 'off', '0']:
            return False

    elif type(x) == int:

        return not x

    return True


def switch(new, curr):
    if new == 'toggle':
        new = {True:False, False:True}[curr]
    else:
        new = x2bool(new)
    return new


def list_remove_by_pattern(l, p):
    l = [x for x in l if p not in x]
    return l


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


def get_pid_cmdline(process_name=''):
    """ gets all the pid and cmdline of the given process name
    """

    pids = []

    for proc in psutil.process_iter():
        try:
            if proc.name() == process_name:
                pids.append( {'pid': proc.pid, 'cmdline': proc.cmdline() } )
        except:
            pass

    return pids


def process_is_running(pattern):
    """ psutil is faster than pgrep in a shell
    """
    for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        try:
            cmdline_list = proc.info["cmdline"]
            if not cmdline_list:
                continue
            cmdline = " ".join(cmdline_list)
            if pattern in cmdline:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def wait4server(timeout=30, port=CONFIG.get('paudio_port', 9990)):

    period = .5
    tries  = int(timeout / period)

    while tries:
        try:
            sp.check_output(f'echo "hello" | nc localhost {port}', shell=True)
            break
        except:
            tries -= 1
            sleep(period)

    if tries:
        return True
    else:
        return False


def wait4source( wanted='', timeout=5 ):
    """ wait until preamp state indicates the wanted source
    """

    tries = timeout

    while tries:
        current = read_state_from_disk().get('source')
        if current == wanted:
            print(f'(common) source has changed to: {wanted}')
            return True
        sleep(1)
        tries -= 1

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
        print(f'{Fmt.GRAY}(pAudio) warning: {str(e)}{Fmt.END}')
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
        print(f'{Fmt.GRAY}(pAudio) warning: {str(e)}{Fmt.END}')
        vol = ''
    return vol


def set_default_device_vol(vol):
    """ only for CoreAudio
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
        print(f'{Fmt.GRAY}(pAudio) Problems setting system volume to MAX on "{dev}"{Fmt.END}')
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
        print(f'{Fmt.GRAY}(pAudio) ERROR with AdjustVolume: {str(e)}{Fmt.END}')
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
        print(f'{Fmt.GRAY}(pAudio) Problems muting on "{dev}"{Fmt.END}')
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
        print(f'{Fmt.GRAY}(pAudio) Problems setting default MacOS playback default device{Fmt.END}')

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
            print("(restore_playback_device_settings) Restoring previous Default Playback Device")
            sp.call(f'SwitchAudioSource -s "{dev}"', shell=True)
        else:
            print("(restore_playback_device_settings) Cannot read `.previous_default_device`")

        # Restore volume
        try:
            with open(f'{MAINFOLDER}/.previous_default_device_volume', 'r') as f:
                vol = f.read().strip()
        except:
            vol = '50'

        if vol:
            print("(restore_playback_device_settings) Restoring previous Playback Device Volume")
            sp.call(f"osascript -e 'set volume output volume '{vol}", shell=True)
        else:
            print(f"{Fmt.GRAY}(start.py) Cannot read `.previous_default_device_volume`{Fmt.END}")


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
    # the IP port name of a remoteXXXX source in config.yml
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


def get_timestamp():
    """ the timestamp string, example: '2025-01-02T08:58:59'
    """
    return datetime.now().isoformat(timespec='seconds')


def time_diff(t1, t2):
    """ input:   <strings> 'MM:SS'
        returns: <int>  the difference in seconds or <string> Error
    """
    try:
        s1 = int(t1[:2]) * 60 + int(t1[-2:])
    except Exception as e:
        return str(e)

    try:
        s2 = int(t2[:2]) * 60 + int(t2[-2:])
    except Exception as e:
        return str(e)

    return s2 - s1


def time_sec2mmss(s, mode=':'):
    """ Format a given float (seconds)

        to      "MM:SS"
        or to   "MMmSSs"    if mode != ':'

        (string)
    """

    if type(s) != float or type(s) != int:
        try:
            s = float(s)
        except:
            s = 0.0

    m = int(s // 60)
    s = int(s % 60)

    if mode == ':':
        return f'{str(m).rjust(2,"0")}:{str(s).rjust(2,"0")}'

    else:
        return f'{str(m).rjust(2,"0")}m{str(s).rjust(2,"0")}s'


def time_sec2hhmmss(x):
    """ Format a given float (seconds) to "hh:mm:ss"
        (string)
    """

    if type(x) != float or type(x) != int:
        try:
            x = float(x)
        except:
            x = 0.0

    h = int( x / 3600 )         # hours
    x = int( round(x % 3600) )  # updating x to reamining seconds
    m = int( x / 60 )           # minutes from the new x
    s = int( round(x % 60) )    # and seconds
    return f'{h:0>2}:{m:0>2}:{s:0>2}'


def time_msec2mmsscc(msec=0, string=''):
    """ Convert milliseconds <--> string MM:SS.CC

        Give me only one parameter: number or string
    """

    if msec and string:
        return 'Error converting msec'


    elif msec:

        if type(msec) != float or type(msec) != int:
            try:
                msec = float(msec)
            except:
                msec = 0.0

        sec  = msec / 1e3
        mm   = f'{sec // 60:.0f}'.zfill(2)
        ss   = f'{sec %  60:.2f}'.zfill(5)

        return f'{mm}:{ss}'


    elif string:

        mm   = int( string.split(':')[0] )
        sscc =      string.split(':')[1]
        ss   = int( sscc.split('.')[0]   )
        cc   = int( sscc.split('.')[1]   )

        millisec = mm * 60 * 1000 + ss * 1000 + cc * 10

        return millisec

