#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    A daemon that listen for relative volume changes,
    then forward them to all remote listener pAudio clients.

    Usage:      remote_volume_daemon.py   start | stop

    NOTE:
        A newcoming remote listener machine will need to send 'hello'
        to this daemon at port <paudio_port> + 5 (usually 9995)
"""

import  sys
import  os
import  socket
import  threading
import  subprocess as sp
from    time import time, sleep
import  json

UHOME           = os.path.expanduser("~")
sys.path.append( f'{UHOME}/pAudio/code/share' )

from    common  import CONFIG, USER, send_cmd, get_my_ip, \
                       read_json_file, tcp_server, Fmt

LOG_DIR           = f'{UHOME}/pAudio/log'
CLIENTS_LIST_PATH = f'{LOG_DIR}/remote_volume_daemon_clients'
REMOTE_CLIENTS    = {}
BASE_PORT         = CONFIG['paudio_port']


def do_ping(addr, timeout=0.1):

    ping_cmd = f"ping -c 1 -W {timeout} {addr}"

    try:
        res = sp.run(ping_cmd.split(), stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        if res.returncode == 0:
            return True

    except Exception as e:
        print(f"(remote_volume_daemon) Error with ping: {e}")

    return False


def get_remote_config(addr, port=BASE_PORT + 1):
    """ Get the config dict from a remote
        pAudio / pe.audio.sys server
        (dict)
    """

    result = {}

    try:
        tmp  = send_cmd('ctrl get_config', host=addr, port=port, timeout=1)

        if not tmp.strip().startswith('{') or not tmp.endswith('}'):
            return result

        result  = json.loads(tmp)

    except Exception as e:
        print(f'(remote_volume_daemon.get_remote_config) {addr}:{port} ERROR: {e}')

    return result


def get_remote_state(addr, port=BASE_PORT):
    """ Get the current state from a remote
        pAudio / pe.audio.sys server
        (dict)
    """

    result = {}

    try:
        tmp  = send_cmd('state', host=addr, port=port, timeout=10)

        if not tmp.strip().startswith('{') or not tmp.endswith('}'):
            return result

        result  = json.loads(tmp)

    except Exception as e:
        print(f'(remote_volume_daemon.get_remote_state) {addr}:{port} ERROR: {e}')

    return result


def get_state():
    return read_json_file(f'{UHOME}/pAudio/.preamp_state')


def remote_is_listening_to_me(remote_state, remote_config):

    if not remote_state or not remote_config:
        return False

    remote_source_name = remote_state.get('source', '')

    remote_app =         remote_state.get('application', '')


    if remote_app == 'pAudio':
        # (i) config.yml has 'remote_addr' but CONFIG has 'ip'
        remote_source_addr = remote_config.get('jack', {})  \
                            .get('sources', {})             \
                            .get(remote_source_name, {})    \
                            .get('ip', '')

    elif remote_app == 'pe.audio.sys':
        remote_source_addr = remote_config.get('sources', {})  \
                            .get(remote_source_name, {})    \
                            .get('jack_pname', '')
    else:
        print(f'{Fmt.RED}(remote_volume_daemon.remote_is_listening_to_me) ERROR {Fmt.END}')
        remote_source_addr = ''


    if 'remote' in remote_source_name.lower() \
        and (my_ip in remote_source_addr or my_hostname in remote_source_addr):

        return True

    else:
        return False


def discover_remotes():
    """ update REMOTE_CLIENTS with remote IPs
        listening to ME as selected remote source
    """

    def find_loudspeaker(lspk):

        res = []

        for k, v in REMOTE_CLIENTS.items():
            if v.get('loudspeaker', '') == lspk:
                res.append(k)

        return res


    save_clients()

    tmp = my_ip.split('.')[:-1]
    my_C_net = '.'.join(tmp) + '.0'

    print(f'(remote_volume_daemon) PLEASE WAIT while scannig {my_C_net} for remote clients ...')

    # do not ping GW
    for n in range(2, 255):

        dest = my_C_net[:-1] + str(n)

        if dest == my_ip:
            continue

        if do_ping(dest):

            remote_state  = get_remote_state(dest)
            remote_config = get_remote_config(dest)

            if remote_is_listening_to_me(remote_state, remote_config):

                rem_loudspeaker = remote_state.get('loudspeaker', '')
                remotes_with_same_loudspeaker = find_loudspeaker( rem_loudspeaker )

                if not remotes_with_same_loudspeaker:
                    REMOTE_CLIENTS[dest] = {'loudspeaker': rem_loudspeaker}
                    save_clients()
                    print(f'(remote_volume_daemon) remote detected {dest}: {rem_loudspeaker} ...')

                else:
                    print(f'(remote_volume_daemon) IP {dest} having the same loudspeaker `{rem_loudspeaker}` as {remotes_with_same_loudspeaker}')

    print(f'(remote_volume_daemon) scannig {my_C_net} DONE.')
    print(f'(remote_volume_daemon) Detected {len(REMOTE_CLIENTS)} remote listening machines')

    if REMOTE_CLIENTS:
        print(json.dumps(REMOTE_CLIENTS, indent=2))
        print( f'(remote_volume_daemon) broadcasting level settings to remotes ...' )
        for addr, info in REMOTE_CLIENTS.items():
            remote_update_levels(addr)


def remote_update_levels(addr):
    """ this is threaded for each destination <addr>,
        but sending each command must be blocking
    """

    def send_levels():
        """ send current local level setting to a remote
        """

        param_list = ['level', 'lu_offset', 'equal_loudness']

        for p in param_list:
            value = get_state().get(p, None)
            if value != None:
                cmd = f'{p} {value}'
                ans = send_cmd(cmd=cmd, host=addr)
                print( f'(remote_volume_daemon) remote {addr} sending \'{cmd}\'; {ans}' )


    job = threading.Thread(
        target = send_levels,
        daemon = True
    )
    job.start()


def stop():
    sp.Popen( f'pkill -u {USER} --older 1 -f "remote_volume_daemon.py"', shell=True )


def save_clients():
    """ to disk """
    with open(CLIENTS_LIST_PATH, 'w') as f:
        f.write( json.dumps(REMOTE_CLIENTS, indent=2) )


def listen_to_preamp():
    """ listen to our local preamp, which relays level commands here at base port + 2
    """

    def relay_level_changes(**kwargs):
        """ Notice that only relative level changes will be relayed
        """

        candidate_cmd = kwargs.get('msg', '')

        # Filtering commands:
        cmd = ''

        # - relative level
        if ('level' in candidate_cmd and 'add' in candidate_cmd):
            cmd = candidate_cmd

        # - LU_offset (usually a toggle command)
        if ('lu_offset' in candidate_cmd):
            cmd = candidate_cmd

        # - equal loudness (usually a toggle command)
        if ('loudness' in candidate_cmd):
            cmd = candidate_cmd

        if not cmd:
            return

        resignations = []
        for addr, info in REMOTE_CLIENTS.items():

            remote_state  = get_remote_state(addr)
            remote_config = get_remote_config(addr)

            if remote_is_listening_to_me(remote_state, remote_config):
                ans = send_cmd(cmd=cmd, host=addr)
                print( f'(remote_volume_daemon) remote {addr} sending \'{cmd}\'; {ans}' )

            else:
                resignations.append([addr, info])

        for addr, info in resignations:
            print( f'(remote_volume_daemon) say bye to remote {addr}:{info} not listening by now :-/' )
            REMOTE_CLIENTS.pop( addr, None )


    print( f'(remote_volume_daemon) Keep relaying level changes to remotes ...' )

    # Start a server listening to LOCAL
    job = threading.Thread(
        target = tcp_server,
        kwargs = {  'addr':         '127.0.0.1',
                    'port':         BASE_PORT + 2,
                    'service_id':   'level_forwarder',
                    'processor':    relay_level_changes
        }
    )
    job.start()


def listen_to_remotes():
    """ remotes says hello here at base port + 5
    """

    def receptionist(**kwargs):
        """ this processor simply accepts a 'hello' message from
            a remote pAudio IP address, then updates REMOTE_CLIENTS
        """

        cli_addr = kwargs.get('addr', '')
        msg      = kwargs.get('msg', '')
        result   = 'nack'

        if not msg or not cli_addr:
            return result

        # Only 'hello' command is processed
        if msg == 'hello':

            if cli_addr != my_ip and '127.0.' not in cli_addr:

                print( f'(remote_volume_daemon) Received hello from: {cli_addr}' )

                if cli_addr not in REMOTE_CLIENTS:

                    sleep(1)
                    cli_state = get_remote_state(cli_addr)
                    REMOTE_CLIENTS[cli_addr] = {'loudspeaker': cli_state.get('loudspeaker', '')}
                    save_clients()

                    print( f'(remote_volume_daemon) Updated remote listening machines:\n'
                           f'{json.dumps(REMOTE_CLIENTS, indent=2)}' )

                # set the level settings in remote listener even if already in REMOTE_CLIENTS
                remote_update_levels(cli_addr)
                result = 'ack'

            else:
                print( f'(remote_volume_daemon) Tas tonto: received \'hello\' '
                       f'from MY SELF ({cli_addr})' )

        return result



    print( f'(remote_volume_daemon) Keep listening for new remotes ...' )

    # Start a server listening to ALL
    job = threading.Thread(
        target = tcp_server,
        kwargs = {  'addr':         '0.0.0.0',
                    'port':         BASE_PORT + 5,
                    'service_id':   'receptionist',
                    'processor':    receptionist
        }
    )
    job.start()


if __name__ == "__main__":

    if sys.argv[1:]:
        if sys.argv[1] == 'stop':
            stop()
            print('(remote_volume_daemon) ended.')
            sys.exit()

        elif sys.argv[1] == 'start':
            stop()

        else:
            print(__doc__)
            sys.exit()
    else:
        print(__doc__)
        sys.exit()


    my_hostname = socket.gethostname()
    my_ip       = get_my_ip()
    if not my_ip:
        print( f'(remote_volume_daemon) ERROR GETTING MY IP ADDRESS !!!')
        exit()

    # this takes a while:
    discover_remotes()

    # these are threaded:
    listen_to_preamp()
    listen_to_remotes()
