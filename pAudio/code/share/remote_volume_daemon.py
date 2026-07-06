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
import  queue
import  subprocess as sp
import  json

UHOME           = os.path.expanduser("~")
sys.path.append( f'{UHOME}/pAudio/code/share' )

from    common  import  *

BASE_PORT         = CONFIG['paudio_port']
LOG_DIR           = f'{UHOME}/pAudio/log'
CLIENTS_LIST_PATH = f'{LOG_DIR}/remote_volume_daemon_clients'
LAN_IP_RANGE      = (2,255) # to discover clients
REMOTE_CLIENTS    = {}


def remote_get_config(addr, port=BASE_PORT):
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
        print(f'{Fmt.RED}(remote_volume_daemon.remote_get_config) {addr}:{port} ERROR: {e}{Fmt.END}')

    return result


def remote_get_state(addr, port=BASE_PORT):
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
        print(f'{Fmt.RED}(remote_volume_daemon.remote_get_state) {addr}:{port} ERROR: {e}{Fmt.END}')

    return result


def remote_lspk_listening_to_me(dest, verbose=True):
    """ Returns the remote loudspeaker name
        if it is listenting to me, else False
    """

    remote_state  = remote_get_state(dest)
    remote_config = remote_get_config(dest)

    if not remote_state:
        if verbose:
            print(f'{Fmt.MAGENTA}(remote_volume_daemon.remote_is_listening_to_me) missing remote_state{Fmt.END}')
        return False

    if not remote_config:
        if verbose:
            print(f'{Fmt.MAGENTA}(remote_volume_daemon.remote_is_listening_to_me) missing remote_config{Fmt.END}')
        return False

    remote_app =         remote_state.get('application', '')

    remote_source_name = remote_state.get('source', '')

    if not 'remote' in remote_source_name.lower():
        return False

    if remote_app == 'pAudio':
        remote_source_addr = remote_config.get('jack', {})      \
                            .get('sources', {})                 \
                            .get(remote_source_name, {})        \
                            .get('remote_addr', '')

    elif remote_app == 'pe.audio.sys':
        remote_source_addr = remote_config.get('sources', {})   \
                            .get(remote_source_name, {})        \
                            .get('jack_pname', '')
    else:
        remote_source_addr = ''

    if not remote_source_addr:
        print(f'{Fmt.RED}(remote_volume_daemon.remote_is_listening_to_me) remote source {remote_source_name}:NO_IP_FOUND {Fmt.END}')
        return False

    if (my_ip in remote_source_addr) or (my_hostname in remote_source_addr):
        return remote_state.get('loudspeaker', 'NO_NAME_LSPK')

    else:
        return False


def remote_clients_add(addr, loudspeaker):
    """ This adds a client to REMOTE_CLIENTS alongside
        threading a queued command manager for it
    """

    REMOTE_CLIENTS[addr] = {
        'loudspeaker':  loudspeaker,
        'queue':        queue.Queue()
    }

    t = threading.Thread(
        target = remote_tcp_comms,
        args   = (addr, )
    )
    t.daemon = True
    t.start()


def remote_clients_remove(addr):
    """ This removes a client from REMOTE_CLIENTS alongside
        putting a POISSON value (None) to its Queue in order
        to terminate its command manager thread.
    """
    lspk = REMOTE_CLIENTS[addr].get('loudspeaker', 'n/a')

    print( f'(remote_volume_daemon) say bye to remote {addr} [{lspk}] not listening by now :-/' )

    REMOTE_CLIENTS[addr]["queue"].put(None)
    REMOTE_CLIENTS.pop( addr, None )


def remotes_discovering():
    """ Initial scan for other pAudio systems
        having myself as the selected source
    """

    def find_loudspeaker(lspk):

        res = []

        for k, v in REMOTE_CLIENTS.items():
            if v.get('loudspeaker', '') == lspk:
                res.append(k)

        return res


    tmp = my_ip.split('.')[:-1]
    my_C_net = '.'.join(tmp) + '.0'

    print(f'(remote_volume_daemon) PLEASE WAIT while scannig {my_C_net} for remote clients ...')

    # do not ping GW
    for n in range(LAN_IP_RANGE[0], LAN_IP_RANGE[1]):

        addr = my_C_net[:-1] + str(n)

        if addr == my_ip:
            continue

        if do_ping(addr):

            rem_loudspeaker = remote_lspk_listening_to_me(addr, verbose=False)

            if rem_loudspeaker:

                remotes_with_same_loudspeaker = find_loudspeaker( rem_loudspeaker )

                if not remotes_with_same_loudspeaker:

                    remote_clients_add(addr, rem_loudspeaker)

                    print(f'{Fmt.BLUE}(remote_volume_daemon) remote detected {addr} [{rem_loudspeaker}] ...{Fmt.END}')

                else:
                    # This is weird, but it can happens if remote machine has more than one IP (eth, wifi)
                    print(f'{Fmt.MAGENTA}(remote_volume_daemon) IP {addr} having the same loudspeaker `{rem_loudspeaker}` as {remotes_with_same_loudspeaker}{Fmt.MAGENTA}')

    print(f'(remote_volume_daemon) scannig {my_C_net} DONE.')
    print(f'(remote_volume_daemon) Detected {len(REMOTE_CLIENTS)} remote listening machines')

    if REMOTE_CLIENTS:

        dump_clients()

        print( f'(remote_volume_daemon) Broadcasting level settings to remotes ...' )
        for addr, info in REMOTE_CLIENTS.items():
            remote_update_levels(addr)


def remote_update_levels(addr):
    """ this is threaded for each destination <addr>,
        but sending each command must be blocking
    """

    def send_levels():
        """ send current local level setting to a remote
        """

        local_state = read_state_from_disk()

        for p in ['level', 'lu_offset', 'equal_loudness']:

            value = local_state.get(p, None)

            if value != None:
                cmd = f'{p} {value}'
                ans = send_cmd(cmd=cmd, host=addr)
                print( f'(remote_volume_daemon) {addr} --> \'{cmd}\'; {ans}' )


    job = threading.Thread(
        target = send_levels,
        daemon = True
    )
    job.start()


def remote_tcp_comms(addr):
    """ This is managed using threads for each client,
        so we can communicate with them by queuing commands.
    """

    q =  REMOTE_CLIENTS[addr]["queue"]

    try:

        # Waits forever until a command has been queued
        while True:

            cmd = q.get()

            if cmd is None:
                q.task_done()
                print( f'(remote_volume_daemon) ending commands threading for: {addr}' )
                break

            ans = send_cmd(cmd=cmd, host=addr)
            print( f'(remote_volume_daemon) {addr} --> \'{cmd}\'; {ans}' )

            q.task_done()

    except Exception as e:
        print(f'(remote_volume_daemon) ERROR sending commnads to {addr}: {e}')


def listen_to_preamp():
    """ listen to our local preamp, which relays level commands here at base port + 2
    """

    def relay_level_changes(**kwargs):
        """ Notice that only relative level changes will be relayed

            kwargs are provided by the server, having keys:
                {'msg': message, 'addr': connected_IP}
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

        for addr in REMOTE_CLIENTS.keys():

            # this queries remote config and state, but it is fast
            if remote_lspk_listening_to_me(addr):

                # Level change commands are queued because their
                # execution on the remote end can be slow.
                REMOTE_CLIENTS[addr]["queue"].put(cmd)

            else:
                resignations.append(addr)

        if resignations:

            for addr in resignations:
                remote_clients_remove(addr)

            dump_clients()


    print( f'(remote_volume_daemon) Keep relaying preamp level changes to remotes ...' )

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

        addr   = kwargs.get('addr', '')
        msg    = kwargs.get('msg', '')

        if not msg or not addr:
            return

        # Only 'hello' command is processed
        if msg == 'hello':

            if addr != my_ip and '127.0.' not in addr:

                print( f'(remote_volume_daemon) Received hello from: {addr}' )

                if addr not in REMOTE_CLIENTS:

                    cli_state = remote_get_state(addr)
                    rem_loudspeaker = cli_state.get('loudspeaker', 'n/a')

                    remote_clients_add(addr, rem_loudspeaker)

                    dump_clients()

                # set the level settings in remote listener even if already in REMOTE_CLIENTS
                remote_update_levels(addr)

            else:
                print( f'(remote_volume_daemon) Tas tonto: received \'hello\' '
                       f'from MY SELF ({addr})' )


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


def dump_clients():
    """ to disk and terminal
    """

    def remote_clients_wo_queues():
        """ ommit queue objets from REMOTE_CLIENTS
            so that it can be JSONified
        """
        rem_clients_copy = {}

        for k ,v in REMOTE_CLIENTS.items():
            rem_clients_copy[k] = {"loudspeaker": REMOTE_CLIENTS[k]["loudspeaker"]}

        return rem_clients_copy


    to_dump = json.dumps(remote_clients_wo_queues(), indent=2)

    print( f'(remote_volume_daemon) Updated remote listening machines:\n'
           f'{to_dump}' )

    with open(CLIENTS_LIST_PATH, 'w') as f:
        f.write( to_dump )


def stop():
    """ kill myself
    """
    sp.Popen( f'pkill -u {USER} --older 5 -f "remote_volume_daemon.py"', shell=True )


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


    my_hostname     = socket.gethostname()
    my_ip           = get_my_ip()
    if not my_ip:
        print( f'{Fmt.RED}(remote_volume_daemon) ERROR GETTING MY IP ADDRESS !!!{Fmt.END}')
        exit()

    # this takes a while
    remotes_discovering()

    # these are threaded:
    listen_to_preamp()
    listen_to_remotes()

