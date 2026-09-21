#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    A pAudio macro to help tuning a Mplayer DVB-T radio channel
"""
from    time            import sleep
import  subprocess      as sp
from    os.path         import expanduser
import  sys
UHOME = expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from    common          import send_cmd, wait4ports, Fmt


ME = 'dvbt_macro'


# DEFAUL
lu_offset = 9
ac3       = False
verbose   = False

def main():

    # Pausing the current player
    send_cmd( f'player pause', sender=ME, verbose=True )

    # Warning message
    send_cmd( f'aux warning clear' )
    send_cmd( f'aux warning set tuning takes a while ...' )

    # Restart Mplayer with the necessary input channels layout
    ac3_flag = '-ac3' if ac3 else ''
    verbose_flag = '-v' if verbose else ''
    sp.call( f'{UHOME}/pAudio/code/share/dvb-t.py start {ac3_flag} {verbose_flag}', shell=True)

    # Tune the radio station
    sp.Popen( f'{UHOME}/pAudio/code/share/dvb-t.py channel "{channel}"', shell=True)

    # Wait a bit for current ports to disappear
    sleep(3)

    # Check for Mplayer ports to re-emerge
    # (some streaming urls take several seconds to load)
    if not wait4ports( f'mplayer_dvb', timeout=10):
        print(f'{Fmt.RED}(radio_macro) ERROR jack ports \'mplayer_dvb\' not found, '
              f'bye :-/{Fmt.END}')
        # Warning message
        send_cmd( f'aux warning clear' )
        sys.exit(-1)

    sleep(.5)

    # Warning message
    send_cmd( f'aux warning clear' )

    # Switching the preamp input
    send_cmd( f'source DVB-T', sender=ME, verbose=True )
    sleep(.5)

    # LU level compensation reference
    send_cmd( f'lu_offset {lu_offset}', sender=ME, verbose=True )
    sleep(.5)
