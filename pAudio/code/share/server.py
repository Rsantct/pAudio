#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    A general purpose TCP server to run a processing module

    Usage:   server.py  <processing_module>  <address>  <port> [-v]

    e.g:     server.py  peaudiosys localhost 9990

    (use -v for VERBOSE debug info printout)
"""

# UNDERSTANDING A SERVER:
# https://realpython.com/python-sockets/#echo-client-and-server
# One thing that’s imperative to understand is that we now have
# a new socket object from accept(). This is important since
# it’s the socket that you’ll use to communicate with the client.
# It’s distinct from the listening socket that the server is using
# to accept new connections. So two sockets are playing at the same time.

import  socket
import  os
import  sys
from    fmt import Fmt
UHOME = os.path.expanduser("~")


# CONFIGURE here the directory path were the processing_module is located
MODULEFOLDER = f'{UHOME}/pAudio/code'

# You can use these properties when importing this module:
SERVICE = ''
CLIADDR = ('', 0)


def handle_client(srv):

    # The connection (the 2nd socket). Notice that accept() is BLOCKING
    global CLIADDR
    con, CLIADDR = srv.accept()

    # The 'with' context will close 'con' on exiting
    with con:
        # Receiving a command phrase
        cmd = con.recv(1024).decode().strip()
        if VERBOSE:
            print( f'(server-{SERVICE}) Rx: {cmd}' )

        # Processing the command and reading the result of execution
        result = PROCESSOR_MOD.do( cmd )

        # Sending back the result
        con.sendall( result.encode() )
        if VERBOSE:
            print( f'(server-{SERVICE}) Tx: {result}' )


def run_server(addr, port):
    # (i) In a future, Python 3.8 will provide a higher level function
    #     'create_server()' that can replace the below 4 commands for
    #     srv creation. In the meanwhile, lets use the well known procedure:

    # Prepare the server (the 1st listening socket)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((addr, port))
    # The backlog option allows to limit the number of future connections
    srv.listen(10)

    # MAIN LOOP to accept, process and close connections.
    while True:
        handle_client(srv)


if __name__ == "__main__":

    try:
        SERVICE, ADDR, PORT  = sys.argv[1:4]
        PORT = int(PORT)
    except:
        print(__doc__)
        sys.exit(-1)

    if '-v' in sys.argv:
        VERBOSE = True
    else:
        VERBOSE = False

    # Importing the service module to be used later when processing commands
    # https://python-reference.readthedocs.io/en/latest/docs/functions/__import__.html
    sys.path.append( MODULEFOLDER )
    PROCESSOR_MOD = __import__(SERVICE)

    print( f'{Fmt.MAGENTA}(server.py) Loading \'{SERVICE}.py\' module, '
           f'listening at {ADDR}:{PORT} ...{Fmt.END}' )
    run_server( ADDR, PORT )
