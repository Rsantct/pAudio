#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    A general purpose TCP server to run a processing module

    Usage:   server.py  <processing_module>  <address>  <port> [-v]

    e.g:     server.py  peaudiosys localhost 9990

    (use -v to include logging info level messages)
"""

import  socket
import  threading
import  logging
import  os
import  sys
from    time import sleep
from    fmt  import Fmt
UHOME = os.path.expanduser("~")


# CONFIGURE here the directory path were the processing_module is located
MODULEFOLDER = f'{UHOME}/pAudio/code'

# You can use these properties when importing this module:
SERVICE = ''
CLIADDR = ('', 0)
CLIENT_TIMEOUT = 5


def handle_client(con, addr):
    """ Handles a client connection on a separate thread
    """

    logging.info(f"(server-{SERVICE}) connected from {addr}")

    try:
        con.settimeout(CLIENT_TIMEOUT)

        data = con.recv(1024)
        if not data:
            return

        cmd = data.decode('utf-8', errors='ignore').strip()
        logging.info(f"(server-{SERVICE}) Rx: {cmd}")


        # just to test the server client threading management
        if cmd.split()[0] == 'wait':
            try:
                seconds = cmd.split()[-1]
                sleep( int(seconds))
                result = f'waited {seconds} sec'
            except Exception as e:
                result = f'{cmd} ERROR: {str(e)}'

        else:
            # If do takes long time, will only affect this client
            result = PROCESSOR_MOD.do(cmd)

        con.sendall(result.encode('utf-8'))
        logging.info(f"(server-{SERVICE}) Tx: {result}")

    except socket.timeout:
        logging.warning(f"(server-{SERVICE}) Timeout with client {addr}")
    except Exception as e:
        logging.error(f"(server-{SERVICE}) Error processing client {addr}: {e}")
    finally:
        con.close()
        logging.info(f"(server-{SERVICE}) closed client {addr}")


def run_server(addr, port):

    global CLIADDR

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        srv.bind((addr, port))
        # backlog increased for safety
        srv.listen(128)
        logging.info(f"(server-{SERVICE}) listening at {addr}:{port}...")

        while True:
            # srv.accept() blocks here, but only until a connection comes in.
            cli_con, CLIADDR = srv.accept()

            # Threading the client
            th_cli = threading.Thread(target=handle_client, args=(cli_con, CLIADDR), daemon=True)
            th_cli.start()

    except KeyboardInterrupt:
        logging.info(f"(server-{SERVICE}) shutting down the server ...")
    finally:
        srv.close()


if __name__ == "__main__":

    try:
        SERVICE, ADDR, PORT  = sys.argv[1:4]
        PORT = int(PORT)
    except:
        print(__doc__)
        sys.exit(-1)

    myLoggingLevel = logging.WARNING

    if '-v' in sys.argv:
        myLoggingLevel = logging.INFO

    # Apply logging level
    logging.basicConfig(level=myLoggingLevel, format='%(asctime)s [%(levelname)s] %(threadName)s: %(message)s')

    # Importing the service module to be used later when processing commands
    # https://python-reference.readthedocs.io/en/latest/docs/functions/__import__.html
    sys.path.append( MODULEFOLDER )
    PROCESSOR_MOD = __import__(SERVICE)

    print( f'{Fmt.BLUE}{Fmt.BOLD}(server.py) Loading \'{SERVICE}.py\' module, '
           f'listening at {ADDR}:{PORT} ...{Fmt.END}' )
    run_server( ADDR, PORT )
