#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" Manage a network linked slave loudspeaker.

    ** BETA VERSION **

    It is assumed a right channel slave 2 ways from jack cpal ports 3 (low) and 4 (high)

    At least a dedicated network must be available:

        Eth     192.168.10.x
        WiFi    192.168.20.x

    Routing:

    LOCAL:                                                REMOTE:
    cpal_client_out:out_1 --> system:playback_1
    cpal_client_out:out_2 --> system:playback_2

    cpal_client_out:out_3 --> right_lspk_send:in_1        zita_recv:1 -> system:pbk_1
    cpal_client_out:out_4 --> right_lspk_send:in_2        zita_recv:2 -> system:pbk_2

    Extra channel for delay measurement
                              right_lspk_send:in_3  -->   zita_recv:3 --\
    right_lspk_recv:out_1                           <--   zita_send:1 --/   loopback

"""

from    common  import *
import  jack


if CONFIG.get('slave_loudspeaker', ''):
    net_link = CONFIG.get('slave_loudspeaker')
else:
    print(f'{Fmt.GRAY}(network_slave_lspk) not configured{Fmt.END}')
    sys.exit()

if net_link == 'eth':
    ZITA_BUFF = 20
    LOCAL_IP  = '192.168.10.1'
    LSPK_IP   = '192.168.10.2'

elif net_link == 'wifi':
    ZITA_BUFF = 50
    LOCAL_IP  = '192.168.20.1'
    LSPK_IP   = '192.168.20.2'

else:
    print("(share/network_lspk) config.yml slave_loudspeaker must be 'eth' or 'wifi'")
    sys.exit()

JCLI = jack.Client('network_lspk', no_start_server=True)
JCLI.activate()


if __name__ == "__main__":

    # Kill zita
    sp.run(['pkill', '-f', 'right_lspk'])
    sleep(.25)

    # Start zita sender
    zita_j2n_cmd = f'zita-j2n --jname right_lspk_send {LSPK_IP} --16bit --chan 3 --ipv4 65000'
    print(f'(share/network_lspk) {zita_j2n_cmd}')
    print(f'(share/network_lspk) zita-j2n sender logs under /tmp')
    out_path = '/tmp/paudio_slave_zita_j2n.out'
    err_path = '/tmp/paudio_slave_zita_j2n.err'
    sp.Popen( f'{zita_j2n_cmd} 1>{out_path} 2>{err_path}', shell=True )
    sleep(1)

    # Wire to camilladsp outputs
    tries = 5
    while tries:
        try:
            JCLI.connect('cpal_client_out:out_2', 'right_lspk_send:in_1')
            JCLI.connect('cpal_client_out:out_3', 'right_lspk_send:in_2')
            break
        except Exception as e:
            pass
        sleep(.2)
        tries -= 1

    if tries:
        print('(share/network_lspk) sender ok')
    else:
        print('(share/network_lspk) sender ERROR')


    # zita receiver
    zita_n2j_cmd = f'zita-n2j --jname right_lspk_recv --chan 1 --buff {ZITA_BUFF} {LOCAL_IP} 65000'
    print(f'(share/network_lspk) {zita_n2j_cmd}')
    print(f'(share/network_lspk) zita-n2j sender logs under /tmp')
    out_path = '/tmp/paudio_slave_zita_n2j.out'
    err_path = '/tmp/paudio_slave_zita_n2j.err'
    sp.Popen( f'{zita_n2j_cmd} 1>{out_path} 2>{err_path}', shell=True )
    sleep(1)

    if process_is_running('zita-n2j --jname right_lspk'):
        print('(share/network_lspk) receiver ok')
    else:
        print('(share/network_lspk) receiver ERROR')
