#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" Manage a network linked loudspeaker,
    for example for the right channel
"""

from    common  import *
import  jack

RIGHT_LSPK = {
    'ip': '192.168.1.71'
}

JCLI = jack.Client('network_lspk', no_start_server=True)
JCLI.activate()


if __name__ == "__main__":

    # Kill zita
    sp.run(['pkill', '-f', RIGHT_LSPK["ip"]])

    # Start zita
    zita_cmd = f'zita-j2n --jname right_lspk {RIGHT_LSPK["ip"]} 65000'
    sp.Popen(zita_cmd.split())
    sleep(.5)

    # Wire to camilladsp outputs
    tries = 5
    while tries:
        try:
            JCLI.connect('cpal_client_out:out_2', 'right_lspk:in_1')
            JCLI.connect('cpal_client_out:out_3', 'right_lspk:in_2')
            break
        except Exception as e:
            print(e)
        sleep(.2)
        tries -= 1

    print('WIP')
