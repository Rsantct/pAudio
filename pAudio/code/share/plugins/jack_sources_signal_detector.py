#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.
"""
    Detector de señal en los puertos JACK de fuentes.

    Envía un mensaje informativo al servidor pAudio
    indicando el puerto en el que se detecta presencia de señal.
"""

import jack
import numpy as np
import socket
from   time import sleep

VERBOSE = False

# pAudio port
PA_PORT = 9990

# Umbral en dB, OjO al ruido de fondo en system (analógico)
THR_DB = -40.0

# Muestras a tomar del buffer de jack
N_SAMPLES   = 100

# Segundos que escucha cada par antes de saltar
TIEMPO_MONITORIZACION = 1

# Flag de aviso entre procesos
audio_detectado = False

client = jack.Client("signal_detector")


def enviar_aviso_tcp(mensaje):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            s.connect(('localhost', PA_PORT))
            s.sendall(mensaje.encode())
    except Exception as e:
        print(f"Error TCP: {e}")


@client.set_process_callback
def process(frames):
    """ Esta función se ejecuta en el hilo de tiempo real de JACK.
        Debe ser lo más rápida posible.
    """

    global audio_detectado

    data = in_port.get_array()[:N_SAMPLES]

    if any(data):
        s = sum( data )
        if s > n_umbral:
            audio_detectado = True


def bucle_escaneo(pnames):

    global audio_detectado

    entrada_detector = 'signal_detector:input'

    last_detected = ''

    with client:

        while True:

            for pname in pnames:

                try:
                    connections = client.get_all_connections(entrada_detector)
                    for p in connections:
                        client.disconnect(p, entrada_detector)
                except:
                    pass

                ports = client.get_ports(pname, is_audio=True, is_output=True)

                try:
                    for p in ports:
                        client.connect(p, entrada_detector)
                    if VERBOSE:
                        print(f"\nescaneando {pname:<20}", end='')

                except Exception as e:
                    print(f"Error: No se pudo conectar a {pname}: {str(e)}")

                audio_detectado = False

                sleep(TIEMPO_MONITORIZACION)

                if audio_detectado:

                    if pname != last_detected:

                        msg = f"signal_detected {pname}"
                        enviar_aviso_tcp(msg)
                        if VERBOSE:
                            print(f"DETECTADO", end='')

                    last_detected = pname


def get_jack_source_clients():
    """ Returns all the found jack readable ports,
        except those in 'exclude_names'
    """

    # Estos nombres de puertos no son fuentes de audio
    excluded_names = [
        'brutefir',
        'cpal_client_out',
        'pre_in_loop',
        'mpd'
    ]

    names = []

    out_ports = client.get_ports(is_output=True, is_audio=True)

    for p in out_ports:

        j_client_name = p.name.split(':')[0]

        if not any(name == j_client_name for name in excluded_names):

            if not j_client_name in names:

                names.append(j_client_name)

    return names


if __name__ == "__main__":

    umbral_lineal = 10 ** (THR_DB / 20) # Conversión a escala lineal
    n_umbral = umbral_lineal * N_SAMPLES

    in_port = client.inports.register("input")

    jack_source_clients = get_jack_source_clients()

    print(f"Iniciando detector con pAudio ...")

    try:
        bucle_escaneo(jack_source_clients)

    except KeyboardInterrupt:
        print("\nDeteniendo detector.")
