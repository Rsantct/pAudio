#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  subprocess as sp
import  psutil
import  threading
from    watchdog.observers  import Observer
from    watchdog.events     import FileSystemEventHandler
import  socket
from    time        import sleep, strftime, perf_counter
from    datetime    import datetime
import  yaml
import  json
import  shlex
from    fmt         import Fmt
import  sys
import  ipaddress
from    getpass     import getuser
from    config      import *

if sys.platform.lower() == 'darwin' and CONFIG.get('coreaudio'):
    from    common_mod  import macos
    macos.CONFIG = CONFIG.copy()

USER = getuser()


class MyYamlIndent(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        # Force lists having indentation relative to the parent, for readability
        return super(MyYamlIndent, self).increase_indent(flow, False)


def loop_file_changed(filepath, what_to_do):

    class MyFileHandler(FileSystemEventHandler):

        def on_modified(self, event):
            # we monitor directories, so we filter for our specific file
            if event.src_path == os.path.abspath(filepath):
                #print(f"✨ Event: {filepath} was modified!")
                self.do_something()


        def do_something(self):
            what_to_do()


    # FSEvents is optimized for directory-level tracking.
    folder_to_watch = os.path.dirname(os.path.abspath(filepath))

    event_handler = MyFileHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=False)

    print(f"(common) 👀  watching for changes to: {filepath}")
    observer.start()


def dict_compare(d1, d2, static=True):
    """ Compare dictionaries
        static: boolean to find only static keys changes, it is FASTER
    """

    if static:
        changes = {k: (d1[k], d2[k]) for k in d1 if k in d2 and d1[k] != d2[k]}
        return changes


    keys1 = set(d1.keys())
    keys2 = set(d2.keys())

    interseccion = keys1.intersection(keys2)

    changed = {k: (d1[k], d2[k]) for k in interseccion if d1[k] != d2[k]}
    added   = {k: d2[k] for k in keys2 - keys1}
    removed = {k: d1[k] for k in keys1 - keys2}

    return changed, added, removed


def json_string_fix(cad):
    """ Example of a raw string that cannot be parsed by json.loads because nested double quotes (")

        {"app":"Spotify","state":"playing","track":"L'elisir d'amore / Act 1: "Signor sargente" - Excerpt","artist":"Gaetano Donizetti","album":"Donizetti:L'elisir d'amore - Highlights","elapsed":19,"duration":161266}'
    """

    for i, c in enumerate(cad):

        if c == '"':

            if cad[i - 1] in ('{', '}', ':'):
                continue

            if cad[i + 1] in ('{', '}'):
                continue

            if cad[i - 2 : i] in ('",'):
                continue

            if cad[i - 1 : i + 1] in (',"'):
                continue

            if cad[i : i + 2] in ('":', '",'):
                continue

            cad = cad[ : i] + "'" + cad[i + 1 :]

    return cad


def get_macros(only_web_macros=True):
    """ Returns the list of executable files under the macros folder.
        By default the list is restricted to web macros kinf of files: "NN_xxxxxx"
    """
    macro_files = []

    with os.scandir( f'{MACROSFOLDER}' ) as entries:

        for entrie in entries:
            fname = entrie.name

            # Only executables files
            if os.path.isfile(f'{MACROSFOLDER}/{fname}') and \
               os.access(f'{MACROSFOLDER}/{fname}', os.X_OK):

                # Web macros are the ones named NN_xxxxxx
                if only_web_macros:
                    if fname.split('_')[0].isdigit():
                        macro_files.append(fname)
                else:
                    macro_files.append(fname)

    macro_files.sort()

    # (i) The web page needs a sorted list (numeric sorting only if NN_xxxxxx items)
    if only_web_macros:
        macro_files.sort( key=lambda x: int(x.split('_')[0]) )

    return macro_files


def get_remote_source_addr_port(src_name):
    """ Gets the ip and port as configured under jack sources
    """
    r_addr = ''
    r_port = 9990

    if CONFIG.get('jack', {}):

        if CONFIG['jack'].get('sources', {}):

            r_src = CONFIG['jack']['sources'].get(src_name, {})
            r_addr = r_src.get('remote_addr', '')
            r_port = r_src.get('remote_port', 9990)

    return r_addr, r_port


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


    def remove_wrap_quotes(x):
        """ removes " for config values
        """

        if type(x) != str:
            return x

        if x[0] == '"' and x[-1] == '"':
            return x[1:-1]


    config = {'port': 6600, 'playlist_directory': f'{UHOME}/.config/mpd/playlists'}


    if not mpd_config_path:
        mpd_config_path = get_running_mpd_config_path()


    if not os.path.isfile(mpd_config_path):
        print(f'(common) read_mpd_config, file NOT found: {mpd_config_path}')
        return {}

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
                        config[section][token] = remove_wrap_quotes(next_token)
                    else:
                        config[token] = remove_wrap_quotes(next_token)

            except ValueError:
                print(f"Error parsing line {lexer.lineno}: {lexer.error_leader()}")
                return {}

            except EOFError: # shlex sometimes raises EOFError
                break

    return config


def get_player_from_source():

    source = read_json_file(PREAMP_STATE_PATH).get('source', 'none')
    lowsource = source.lower()

    if 'spotify' in lowsource:

        if any('librespot' in p for p in CONFIG['plugins']):
            player = 'librespot'
        else:
            player = 'spotify'

    elif 'librespot' in lowsource:
        player = 'librespot'

    elif 'mpd' in lowsource or lowsource == 'cd':
        player = 'mpd'

    elif 'tdt' in lowsource or 'dvb' in lowsource:
        player = 'mplayer'

    elif source[:6] == 'remote':
        player = source

    else:
        jport = CONFIG["sources"].get(source, {}).get('jport', '')

        if 'mpd' in jport:
            player = 'mpd'

        else:
            player = ''

    return player


def get_web_config():

    # LU_monitor_enabled is a legacy option, currently it is always enabled.

    result = {  'main_selector':        'sources',
                'LU_monitor_enabled':   True,
                'onoff':                'pAudio',
                'monkey_button':        'toggle',
                'user_macros':          get_macros()
    }

    try:
        cfg = read_yaml_file(CONFIG_PATH)

        for item, value in cfg.get('web_config', {}).items():
            result[item] = value

    except Exception as e:
        print(f'{Fmt.RED}(common.get_web_config) ERROR: {str(e)}{Fmt.END}' )

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


    AMP_CMD     = CONFIG.get('amplifier_switch', {}).get('command', '~/bin/ampli.sh')

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


def detect_sound_card_io(alsa_dev):
    """ Detect the recording and playback capabilities of the sound card
        returns: 'recplay' | 'rec' | 'play' | ''
    """

    arecord = aplay = ''
    try:
        arecord = sp.check_output('arecord -l'.split()).decode()
    except:
        pass
    try:
        aplay = sp.check_output('aplay -l'.split()).decode()
    except:
        pass

    cname = alsa_dev.replace('hw:','').split(',')[0]

    if cname in arecord and cname in aplay:
        return 'recplay'
    elif cname in arecord and not cname in aplay:
        return 'rec'
    elif not cname in arecord and cname in aplay:
        return 'play'
    else:
        return ''


def restore_sound_card():
    """
        Only works for Linux-ALSA

        This assumes that you have set your alsamixer levels and saved them to:
            ~/pAudio/alsactl.<YOUR_ALSA_CARD_NAME>
    """

    with open(f'{UHOME}/pAudio/config.yml', 'r') as f:
        pa_config = yaml.safe_load( f.read() )

    if not pa_config.get('jack'):
        return

    alsa_device = pa_config["jack"]["device"]
    # example: hw:UDJ6,0

    alsa_name = alsa_device.split(',')[0].split(':')[-1]

    alsactl_path =  f'{UHOME}/pAudio/alsactl.{alsa_name}'

    cmd = f'alsactl --file {alsactl_path} restore {alsa_name}'

    if os.path.isfile(alsactl_path):
        print(f'{Fmt.GREEN}(common) trying to restore \'{alsa_name}\' sound card settings: {alsactl_path}{Fmt.END}')
        try:
            sp.call(cmd, shell=True)
        except Exception as e:
            print(f'{Fmt.BOLD}(common) Error restoring \'{alsa_name}\': {str(e)}{Fmt.END}')

    else:
        print(f'{Fmt.RED}(common) \'{alsa_name}\' sound card settings file not found: {alsactl_path}{Fmt.END}')


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


def check_output(host, port, message, timeout=1.0, chunk_size=4096):
    """
    Envía 'message' a (host, port) vía TCP y devuelve la respuesta completa
    como string, similar a subprocess.check_output().
    """

    if not host or not port or not message:
        return ''

    data = b''

    try:
        with socket.create_connection((host, port)) as conn:

            conn.settimeout(timeout)

            if isinstance(message, str):
                message = message.encode()

            conn.sendall(message)

            while True:
                try:
                    chunk = conn.recv(chunk_size)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break

    except Exception as e:
        pass

    return data.decode()


def send_cmd( cmd, sender='', verbose=False, timeout=3, host=CONFIG["paudio_addr"], port=CONFIG["paudio_port"] ):
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
    """ wrapper for reading the playing info and metadata dict
        (dictionary)
    """
    return read_json_file(PLAYER_INFO_PATH)


def read_cdda_meta_from_disk():
    """ wrapper for reading the cdda info and metadata dict from disk
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


def save_json_file(d, fpath, timeout=.5):
    """ Some json files cannot be ready to write because concurrency,
        so let's retry
    """
    period = 0.1
    tries = int( round(timeout / period) )

    while tries:
        try:
            with open(fpath, 'w') as f:
                d['timestamp'] = get_timestamp()
                f.write( json.dumps(d, indent=2) )
            return True
        except:
            tries -= 1
            sleep(period)

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


def wait4server(timeout=30, verbose_seconds=5, port=CONFIG.get('paudio_port', 9990)):

    elapsed = 0
    period = .5
    tries  = int(timeout / period)

    print(f'{Fmt.GRAY}{Fmt.BOLD}{Fmt.ITALIC}Wainting {timeout } s for server response ...{Fmt.END}')

    while tries:

        if check_output('localhost', port,' hello'):
            break

        if elapsed and not elapsed % verbose_seconds:
            print(f'{Fmt.GRAY}{Fmt.ITALIC}elapsed {elapsed} s for server response ...{Fmt.END}')

        sleep(period)
        elapsed += period
        tries -= 1

    if tries:
        print(f'{Fmt.GRAY}{Fmt.BOLD}{Fmt.ITALIC}Server response was in {elapsed} s{Fmt.END}')
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


def get_benkmarch(n=500e3):
    """ Calculate a CPU benchmark referring to Intel Core i3

                          meas    estimated
                          delay   bench
                          500e3   500e3
                          -----   -----
        RPI 3 B           0.895   0.05
        RPI 3 B+          0.450   0.11
        Asus Atinker      0.225   0.22
        Core i3           0.049   1.0
        Apple M1          0.032   1.5
    """

    start = perf_counter()
    _ = sum(i**2 for i in range(int(n)))
    end = perf_counter()

    cpu_score = end - start

    # choosing Core i3 as reference
    reference_score = 0.049

    return 1 / (cpu_score / reference_score)


def estimate_server_response_delay():
    """ See the table (experimental):

                          estimated
                          bench       time to run
                          500e3       the pAudio server
                          -----       -----
        RPI 3 B           0.05        36 s
        RPI 3 B+          0.11        27 s
        Asus Atinker      0.22        16 s
        Core i3           1.0          4 s
        Apple M1          1.5          2 s

    """

    my_bm = get_benkmarch(n=500e3)

    # Exp function to find the estimated time of response
    estimated = 4.88 * (my_bm ** -0.72)

    estimated = int(round(estimated, 1))

    print(f'{Fmt.GRAY}{Fmt.BOLD}{Fmt.ITALIC}(i) Estimated server response is {estimated} s about{Fmt.END}')

    return estimated


def ip_is_reachable(ip):
    """ ip (str) responds to a ping request.
        (boolean)
    """
    param = '-n' if sys.platform.lower().startswith('win') else '-c'

    command = ['ping', param, '1', ip]

    # Run the command and redirect output to DEVNULL to keep the console clean
    result = sp.run(command, stdout=sp.DEVNULL, stderr=sp.DEVNULL).returncode == 0

    return result


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


def get_camilladsp_last_error():
    """
    --> Al iniciar pAudio con el DAC apagado
    2025-12-06 22:36:50.131948 ERROR [src/bin.rs:293] Playback error: Could not find playback device 'E30 II'

    --> Al apagar el DAC con pAudio arrancado
    2025-12-06 22:40:34.001230 ERROR [src/bin.rs:293] Playback error: Playback device is no longer alive

    Devuelve un DICT: {'date':'', 'time':'', 'error':''}
    """

    res = {'date':'', 'time':'', 'error':''}

    try:

        lines = read_last_lines(f'{LOGFOLDER}/camilladsp.log', 100)

        for line in lines[::-1]:

            linesplit = line.split()

            if 'ERROR' in linesplit:
                res["date"]  = linesplit[0]
                res["time"]  = linesplit[1]
                res["error"] = ' '.join( linesplit[4:] )
                break

    except Exception as e:
        print(f'(common.get_last_camilladsp_error) {str(e)}')

    return res


def find_zita_link_ports(source_name):
    """ A helper to read zita_link addressing data from the auxiliary file:
            log/zita_link_udp_ports
    """

    result = ('', 0, 0)

    try:
        with open(f'{LOGFOLDER}/zita_link_udp_ports', 'r') as f:
            zita_remotes = json.loads( f.read() )
            zita_remote = zita_remotes[source_name]
            result = ( zita_remote["addr"], zita_remote["port"], zita_remote["udpport"] )

    except Exception as e:
        print(f'{Fmt.RED}(common) Error reading log/zita_link_udp_ports for source `{sname}`: {str(e)}{Fmt.END}')

    return result


def zita_remote_restart(raddr='', ctrl_port=0, zita_port=0, mode='restart'):
    """
        Restarting zita-j2n on the multiroom sender's end,
        pointing to our ip.

        (i) The sender will run zita_j2n only when a receiver request it
    """

    if mode == 'stop':

        zargs = json.dumps( (get_my_ip(), None, 'stop') )
        remotecmd = f'aux zita_j2n {zargs}'

        result = send_cmd(remotecmd, host=raddr, port=ctrl_port, timeout=1)

        if CONFIG["verbose"]:
            print(f'{Fmt.GRAY}(common) stopping remote {raddr}: {remotecmd}. Response was: {Fmt.BOLD}{result}{Fmt.END}')

        return result


    zargs     = json.dumps( (get_my_ip(), zita_port, 'start') )
    remotecmd = f'aux zita_j2n {zargs}'
    result = send_cmd(remotecmd, host=raddr, port=ctrl_port)

    print(f'{Fmt.GRAY}(common) SENDING TO REMOTE: {remotecmd}. Response was: {Fmt.BOLD}{result}{Fmt.END}')

    return result


def zita_local_restart(raddr='', udp_port=65000, buff_size=20, mode='restart', jport=''):
    """
        Run zita-n2j listen ports on the multiroom receiver's end.

        (i) Will log zita process printouts under LOGFOLDER
    """

    def do_stop():

        if CONFIG["verbose"]:
            print(f'{Fmt.GRAY}(common) killing local zita-n2j: {jport}{Fmt.END}')

        zitapattern  = f'zita-n2j --jname {jport}'

        try:
            sp.call( ['pkill', '-KILL', '-u', USER, '-f',  zitapattern] )
            return 'done'
        except Exception as e:
            return str(e)


    if not jport:
        jport = f'zita_n2j_{ raddr.split(".")[-1] }'
    zitacmd = f'zita-n2j --jname {jport} --buff {buff_size} {get_my_ip()} {udp_port}'
    zitalog = f'{LOGFOLDER}/{jport}.log'

    # jport is used for mode=stop
    if not jport and not (raddr and udp_port):
        print(f'{Fmt.RED}(common) zita_local_restart bad arguments{Fmt.END}')
        return 'bad arguments'

    tmp = do_stop()

    if mode == 'stop':
        return tmp

    # Assign ALIAS to JACK ports to be able to switch by using
    # the IP port name of a remoteXXXX source in config.yml
    #
    try:
        # Using stdbuf because zita does use unbuffered output to tty, skipping stdout/stderr
        sp.Popen( f'stdbuf -oL -eL {zitacmd} 1>{zitalog} 2>&1', shell=True )
        wait4ports(jport, 3)
        sp.Popen( f'jack_alias {jport}:out_1 {raddr}:out_1'.split() )
        sp.Popen( f'jack_alias {jport}:out_2 {raddr}:out_2'.split() )
        print(f'{Fmt.GRAY}(common) RUNNING LOCAL: {zitacmd}, {Fmt.BOLD}LOGGING under {LOGFOLDER}{Fmt.END}')
        return 'done'

    except Exception as e:
        print(f'{Fmt.RED}(common) zita_local_restart ERROR: {e}{Fmt.END}')
        return str(e)


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

