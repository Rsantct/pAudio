#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.
"""
    Signal detector for JACK ports of sources.

    Sends an informational message to the pAudio server
    indicating the port where a signal is detected.

    Options:

        -v      verbose

        -s      displays the detected sources on JACK and terminates

    Configuration file:

        jack_sources_signal_detector.yml

"""

import  sys
import  os
import  jack
import  numpy as np
import  socket
import  json
import  yaml
from    time import sleep, time


client        = jack.Client("signal_detector")
in_port       = client.inports.register("input")
verbose       = False
n_channels    = 2
flag_detected = False


def get_config():

    global  cfg

    cfg = {}

    default_cfg = {
        # Detection threshold in dB.
        # Pay attention to background noise in system (A/D)
        # if using a card with input ports.
        'thr_db': -40.0,

        # Samples to take from the jack buffer to speed up
        # CPU usage in the 'jack_monitor' callback
        'n_samples': 100,

        # Seconds of listening before moving on to the next source.
        'monitor_time': 1,

        # Monitor the <system:input> port
        'system_input': True,

        # pAudio backend TCP port
        'pa_port': 9990
    }

    my_fname = __file__
    my_dir = os.path.dirname(my_fname)
    my_name = os.path.basename(my_fname)[:-3]

    config_dir = f'{my_dir}/{my_name}'
    config_path = f'{config_dir}/{my_name}.yml'

    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    if not os.path.isfile(config_path):
        print(f'Saving default config to {config_path}')
        with open(config_path, 'w') as f:
            f.write( yaml.safe_dump(default_cfg) )
        cfg = default_cfg

    else:
        with open(config_path, 'r') as f:
            cfg = yaml.safe_load( f.read() )


def send_msg(mensaje):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            s.connect(('localhost', cfg["pa_port"]))
            s.sendall(mensaje.encode())
    except Exception as e:
        print(f"Error TCP: {e}")


def get_jack_source_clients():
    """ Returns all the found jack readable ports,
        except those in 'reserved_names'

        This takes about 1.5 ms in a Raspberry Pi 3
    """

    # Nombres de puerto reservados (no son fuentes de audio)
    reserved_names = [
        'brutefir',
        'cpal_client_out',
        'pre_in_loop',
        'mpd'
    ]

    if not cfg["system_input"]:
        reserved_names.append('system')

    clients = {}
    names = []

    out_ports = client.get_ports(is_output=True, is_audio=True)

    for p in out_ports:

        p_name = p.name.split(':')[0]

        if not any(reserved_name == p_name for reserved_name in reserved_names):

            if not p_name in names:
                names.append(p_name)
                clients[p_name] = []

            clients[p_name].append(p)

    return clients


def clear_port_connections(p):
    """ disconnect any port from <signal_detector:input>
    """
    try:
        connections = client.get_all_connections(p)
        for cp in connections:
            client.disconnect(cp, p)
    except:
        pass


# JACK REAL TIME CALLBAK
@client.set_process_callback
def jack_monitor(frames):
    """ (i) This function runs on the JACK real-time thread,
            therefore it must be as lightweight as possible.

        It simply sets the flag.
    """

    global flag_detected

    # We only took a few samples to speed up this routine.
    data = in_port.get_array()[:cfg["n_samples"]]

    # simplified detector, without rms math or similar
    if any(data):
        acc = sum( data )
        if acc > acc_thr:
            flag_detected = True


# MAIN LOOP
def scan_loop():

    global flag_detected

    last_detected = ''

    with client:

        while True:

            jclients = get_jack_source_clients()

            for pname, ports in jclients.items():

                clear_port_connections(in_port)

                n_channels = len(ports)

                try:
                    for p in ports:
                        client.connect(p, in_port)
                    if verbose:
                        print(f"\nscanning {pname:<20}", end='')

                except Exception as e:
                    print(f"Error connecting: {str(e)}")

                flag_detected = False

                # We update the accumulated threshold, which depends on
                # the number of channels from the source we have connected
                # to the monitor input (usually 2 stereo channels).
                acc_thr = thr_lin * cfg["n_samples"] / n_channels

                # During this sleep, the 'jack_monitor' callback will
                # set the flag 'flag_detected' if it detects any signal
                sleep( cfg["monitor_time"] )

                if flag_detected:

                    if pname != last_detected:

                        msg = f"signal_detected {pname}"
                        send_msg(msg)
                        if verbose:
                            print(f"DETECTED", end='')

                    last_detected = pname


if __name__ == "__main__":

    get_config()

    only_view_jack_sources = False

    for opc in sys.argv[1:]:

        if '-h' in opc:
            print(__doc__)
            sys.exit()

        if opc == '-v':
            verbose = True

        elif opc == '-s':
            only_view_jack_sources = True


    if only_view_jack_sources:
        t0 = time()
        clients = get_jack_source_clients()
        t_ms = round((time() - t0) * 1000, 2)
        if verbose:
            print(f'Elapsed time to get jack sources: {t_ms} ms')
        for k, v in clients.items():
            clients[k] = [p.name for p in v ]
        print(json.dumps(clients, indent=2))
        sys.exit()


    print(f"Starting JACK sources signal detector ...")
    thr_lin = 10 ** (cfg["thr_db"] / 20)
    acc_thr = thr_lin * cfg["n_samples"] / n_channels

    try:
        scan_loop()

    except KeyboardInterrupt:
        print("\nStopping detector.")
