#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a CC based personal audio system.

""" A naive tool to visualize camillaDSP pAudio settings in runtime
"""

import  os
import  sys
from    time import sleep
import  json
from    camilladsp import CamillaClient

UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/pAudio/code/share')

from fmt import Fmt

CC = CamillaClient("127.0.0.1", 1234)

# Código ANSI para mover el cursor a la esquina superior izquierda
CURSOR_HOME = "\033[H"


def get_drc_filters_type(c, drc_names):

    ftypes = []

    for fname in drc_names:
        t = c["filters"][fname]["type"]
        ftypes.append(t)

    return ' '.join(list(set(ftypes)))


def print_things():

    vol     = CC.volume.main_volume()
    muted   = CC.volume.main_mute()

    state   = CC.general.state().name
    load    = round( CC.status.processing_load(), 1 )

    c       = CC.config.active()

    chunk_size = c.get('devices', {}).get('chunksize', 0)

    if c.get('devices', {}).get('capture', {}):
        cap_dev = c['devices']['capture']['device']
    else:
        cap_dev = '--'

    if c.get('devices', {}).get('playback', {}):
        pbk_dev = c['devices']['playback']['device']
    else:
        pbk_dev = '--'

    level     = CC.levels.capture_peak()

    # pAudio stuff
    gainL       = c["filters"]["bal_pol_L"]["parameters"]["gain"]
    gainR       = c["filters"]["bal_pol_R"]["parameters"]["gain"]
    balance     = - gainL + gainR

    drc_gain    = c["filters"]["flat_gain_drc"]["parameters"]["gain"]
    lu_offset   = c["filters"]["lu_offset"]["parameters"]["gain"]
    source_gain = c["filters"]["source_gain_offset"]["parameters"]["gain"]
    delay       = c["filters"]["preamp_delay"]["parameters"]["delay"]

    pp = c["pipeline"]

    # pipeline steps scheme
    #   L   R
    #     0      compressor
    #     1      channel mapping and polarity
    #   2   3    gains, eq (loudness, tones, house_curve) , delay
    #   .   .    lspk eq (same set for L and R) OPTIONAL STEP
    #   .   .    drc filters                    POSITION DEPENDS ON lspk eq

    # Let's retrieve some pipeline indexes
    lspk_eq_L_step = 0
    lspk_eq_R_step = 0
    drc_L_step = 0
    drc_R_step = 0
    for i, step in enumerate(pp):
        if 'DRC left' in step["description"]:
            drc_L_step = i
        if 'DRC right' in step["description"]:
            drc_R_step = i
        if '(EQ left)' in step["description"]:
            lspk_eq_L_step = i
        if '(EQ right)' in step["description"]:
            lspk_eq_R_step = i


    drc_L_typeOfFilters = get_drc_filters_type( c, pp[drc_L_step]["names"] )
    drc_R_typeOfFilters = get_drc_filters_type( c, pp[drc_R_step]["names"] )

    drc_L_numberOfFilters = len(pp[drc_L_step]["names"])
    drc_R_numberOfFilters = len(pp[drc_R_step]["names"])

    if lspk_eq_L_step > 3:
        lspk_eq = pp[lspk_eq_L_step]["names"]
    else:
        lspk_eq = 'n/a'

    muted = f'{Fmt.BOLD}(muted){Fmt.END}' if muted else '       '

    # Visualize from the top of the terminal
    sys.stdout.write(CURSOR_HOME)

    print(f'{Fmt.BOLD}--- pAudio{Fmt.END}')
    print()
    print(f'{Fmt.BOLD}COMPRESSOR:     {Fmt.END}', not pp[0]["bypassed"])
    print()
    print(f'{Fmt.BOLD}PREAMP (L/R):{Fmt.END}')
    print(f'source_gain:    {source_gain:5.1f}')
    print(f'delay:          {delay:5.1f}')
    print(f'LU_offset:      {lu_offset:5.1f}')
    print(f'balance:        {balance:5.1f}')
    print()
    print(f'{Fmt.BOLD}LOUDSPEAKER EQ (L/R):{Fmt.END}')
    print(f'{lspk_eq}')
    print()
    print(f'{Fmt.BOLD}DRC{Fmt.END} (gain {drc_gain:5.1f} dB):')
    print('L:', f'{drc_L_numberOfFilters:2d} x', drc_L_typeOfFilters)
    print('R:', f'{drc_R_numberOfFilters:2d} x', drc_R_typeOfFilters)
    print()
    print(f'{Fmt.BOLD}--- CamillaDSP{Fmt.END}')
    print()
    print(f'buffer:  {chunk_size:4d}')
    print(f'capture: {cap_dev:<15} playback: {pbk_dev}')
    print(f'state:   {state:<15}')
    print(f'load:    {Fmt.BG_YELLOW}{Fmt.BOLD}{Fmt.BLACK}{load:4.1f} %{Fmt.END}')
    print()
    print(f'input signal peak: {level[0]:7.1f} {level[1]:7.1f} ')
    print(f'main volume:       {vol:7.1f} {muted}')
    print()

    # force the terminal to display the changes immediately
    sys.stdout.flush()



if __name__ == "__main__":

    os.system('cls' if os.name == 'nt' else 'clear')

    CC.connect()

    while True:
        print_things()
        sleep(1)
