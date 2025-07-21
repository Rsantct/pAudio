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

from    subprocess import Popen
from    time import time
import  socket
from    watchdog.observers import Observer
from    watchdog.events import FileSystemEventHandler
import  sys
import  os
import  json

UHOME           = os.path.expanduser("~")
sys.path.append( f'{UHOME}/pAudio/code/share' )

import  server
from    common  import CONFIG, USER, send_cmd, read_json_file, read_last_line

LOG_DIR         = f'{UHOME}/pAudio/log'
CMD_LOG_PATH    = f'{LOG_DIR}/paudio_cmd.log'


# ------------- USER CONFIG --------------
# x.x.x.RANGE
REMOTES_ADDR_RANGE = range(40, 59)
# ----------------------------------------


# Generic handler from 'watchdog' for doing actions when a file change occurs
class file_event_handler(FileSystemEventHandler):
    """ Will do something when a <fname> change occurs
    """
    # (i) This is an inherited class from the imported one 'FileSystemEventHandler',
    #     which provides the 'event' propiertie.
    #     Here we expand the class with our custom parameters:
    #     'fname' and wanted 'action'

    def __init__(self, fname, action, antibound=True):
        self.fname      = fname
        self.action     = action
        self.antibound  = antibound
        self.ts         = time()

    def on_modified(self, event):
        # DEBUG
        #print( f'(i) event type: {event.event_type}, file: {event.src_path}' )
        if event.src_path == self.fname:
            if self.antibound:
                if (time() - self.ts) > .1:
                    globals()[self.action]()
                self.ts = time()
            else:
                    globals()[self.action]()


def get_remote_selected_source(addr, port=9990, timeout=0.5):
    """ Gets the selected source from a remote pAudio server at <addr:port>
        (string)
    """
    remote_source = ''
    try:
        tmp  = send_cmd('state', host=addr, port=port, timeout=timeout)

        if not tmp.startswith('{') or not tmp.endswith('}'):
            return remote_source

        remote_state  = json.loads(tmp)

        # former pe.audio.sys project: 'source' was 'input'
        remote_source = remote_state.get('source', '')
        if not remote_source:
            remote_source = remote_state.get('input', '')

    except Exception as e:
        print(f'(remote_volume.get_remote_selected_source) Exception: {str(e)}')

    return remote_source


def get_state():
    return read_json_file(f'{UHOME}/pAudio/.preamp_state')


def detect_remotes():
    """ list of remote IPs listening to a source named *remote*
    """
    clients = []

    for n in REMOTES_ADDR_RANGE:

        addr_list = my_ip.split('.')
        addr_list[-1] = str(n)
        addr = '.'.join( addr_list )

        if addr == my_ip:
            continue

        if 'remote' in get_remote_selected_source(addr).lower():
            clients.append(addr)

    return clients


def remote_send_cmd(cli_addr, cmd):
    print( f'(remote_volume) remote {cli_addr} sending \'{cmd}\'' )
    send_cmd( cmd, host=cli_addr, verbose=False )


def remote_update_levels(rem_addr):
    level           = get_state()["level"]
    lu_offset       = get_state()["lu_offset"]
    equal_loudness  = get_state()["equal_loudness"]
    remote_send_cmd(rem_addr, f'lu_offset {lu_offset}')
    remote_send_cmd(rem_addr, f'loudness {equal_loudness}')
    remote_send_cmd(rem_addr, f'level {level}')


# The action triggered by the observer
def relay_level_changes():
    """ Notice that only relative level changes will be relayed
    """

    # Read last command from the command log file
    tmp = read_last_line( CMD_LOG_PATH )
    # e.g.: "2020/10/23 17:16:43; level -1 add; done"
    last_cmd = tmp.split(';')[1].strip()

    # Filtering commands:
    wanted_cmd = ''

    # - relative level
    if ('level' in last_cmd and 'add' in last_cmd):
        wanted_cmd = last_cmd

    # - LU_offset (usually a toggle command)
    if ('lu_offset' in last_cmd):
        lu_offset       = get_state()["lu_offset"]
        wanted_cmd      = f'lu_offset {lu_offset}'

    # - equal loudness (usually a toggle command)
    if ('loudness' in last_cmd):
        equal_loudness  = get_state()["equal_loudness"]
        wanted_cmd      = f'loudness {equal_loudness}'

    # Early return
    if not wanted_cmd:
        return

    # Forwarding commands to remotes
    for rem_addr in remoteClients:

        # Checking if remote is still listening to us
        # then updates the level event to remote
        if 'remote' in get_remote_selected_source(rem_addr):
            remote_send_cmd(rem_addr, wanted_cmd)

        # else purge from remotes list if not listening anymore
        else:
            print( f'remote {rem_addr} not listening by now :-/' )
            remoteClients.remove( rem_addr )
            print( f'Updated remote listening machines: {remoteClients}' )


# Broadcast level settings to all remote machines
def broadcast_level_settings():

    for rem_addr in remoteClients:

        if 'remote' in get_remote_selected_source(rem_addr):
            remote_update_levels(rem_addr)
        else:
            print( f'remote {rem_addr} not listening by now :-/' )
            remoteClients.remove( rem_addr )
            print( f'Updated remote listening machines: {remoteClients}' )


# The action called from our instance of <server.py> when receiving messages.
# (See below 'server.MODULE=...' when initiating <server.py> )
def do(cmd):

    cli_addr = server.CLIADDR[0]
    result = 'nack'

    # Only 'hello' command is processed
    if cmd == 'hello':
        if cli_addr != my_ip and '127.0.' not in cli_addr:
            print( f'(remote_volume) Received hello from: {cli_addr}' )
            if cli_addr not in remoteClients:
                # updating new client into remote clients list
                remoteClients.append(cli_addr)
                print( f'(remote_volume) Updated remote listening machines: '
                       f'{remoteClients}' )
            # set the level settings in remote listener even if already in remoteClients
            remote_update_levels(cli_addr)
            result = 'ack'
        else:
            print( f'(remote_volume) Tas tonto: received \'hello\' '
                   f'from MY SELF ({cli_addr})' )

    return result


def killme():
    Popen( f'pkill -u {USER} -f "remote_volume_daemon.py start"', shell=True )
    sys.exit()


if __name__ == "__main__":

    # Reading command line
    if sys.argv[1:]:
        if sys.argv[1] == 'stop':
            killme()
        elif sys.argv[1] == 'start':
            pass
        else:
            print(__doc__)
            sys.exit()
    else:
        print(__doc__)
        sys.exit()


    # Retrieving basic data for this to work
    my_hostname     = socket.gethostname()
    my_ip           = socket.gethostbyname(f'{my_hostname}.local')
    remoteClients   = detect_remotes()
    print( f'(remote_volume) Detected {len(remoteClients)} '
           f'remote listening machines: {remoteClients}' )

    # Broadcast level settings to remote clients
    print( f'(remote_volume) broadcast level settings to remotes ...' )
    broadcast_level_settings()

    #   WATCHDOG to observe file changes
    #   https://watchdog.readthedocs.io/en/latest/
    #   https://stackoverflow.com/questions/18599339/
    #   python-watchdog-monitoring-file-for-changes
    #   Use recursive=True to observe also subfolders
    #   Even observing recursively the CPU load is negligible,
    #   but we prefer to observe to a single folder.
    observer = Observer()
    observer.schedule( file_event_handler(  fname=CMD_LOG_PATH,
                                            action='relay_level_changes',
                                            antibound=True ),
                                            path=LOG_DIR,
                                            recursive=False )
    observer.start()

    print( f'(remote_volume) Keep relaying level changes to remotes ...' )


    # A server that listen for new remote listening clients to emerge
    print( f'(remote_volume) Keep listening for new remotes ...' )
    server.SERVICE       = 'remote_volume_daemon'
    server.PROCESSOR_MOD = __import__(__name__)
    server.VERBOSE       = True
    server.run_server( '0.0.0.0', CONFIG['paudio_port'] + 5)
