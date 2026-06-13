#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" A naive tool to visualize pAudio and camillaDSP in runtime
"""

import  os
import  sys
import  subprocess as sp
from    time import sleep
import  json
import  yaml
import  psutil
from    camilladsp import CamillaClient

UHOME = os.path.expanduser('~')
sys.path.append(f'{UHOME}/pAudio/code/share')
from fmt import Fmt

if sys.platform == 'linux':

    def get_jack_version():
        tmp = sp.run(['jackd', '--version'], capture_output=True, text=True)
        return tmp.stdout.strip()

    def get_jack_parameters():

        res = ''
        tmp = []

        for proc in psutil.process_iter(['name', 'cmdline']):
            if proc.info['name'] == 'jackd':
                tmp = proc.info['cmdline']

        # ['jackd', '-d', 'alsa', '-P', 'hw:UDJ6,0', '-r', '48000', '-p', '1024', '-n', '2', '-z', 'shaped', '--softmode']

        hw_found = False
        for x in tmp:
            if not hw_found:
                hw_found = 'hw:' in x
            if hw_found:
                res += f' {x}'

        return res.strip()


    import  jack

    try:
        JC = jack.Client(name='paudio_camilladsp_viewer', no_start_server=True)
    except:
        print(f'{Fmt.BOLD}Jack not detected{Fmt.END}')
        sys.exit()

    jack_RT         = 'RT' if JC.realtime else '  '
    jack_rate       = JC.samplerate
    jack_period     = JC.blocksize
    jack_parameters = get_jack_parameters()
    jack_version    = get_jack_version()


# Códigos ANSI para manipular el terminal
#   mover el cursor a la esquina superior izquierda
CURSOR_HOME = "\033[H"
CURSO_HIDE  = "\033[?25l"
CURSO_SHOW  = "\033[?25h"


def get_cpu_pcent(interval=0.25):
    p = psutil.cpu_percent(interval=interval)
    return p


def get_drc_filters_type(c, drc_names):

    ftypes = []

    for fname in drc_names:
        t = c["filters"][fname]["type"]
        ftypes.append(t)

    return ' '.join(list(set(ftypes)))


def get_pa_config():
    """ get pAudio config """

    global PA_CONFIG

    try:
        with open(f'{UHOME}/pAudio/config/config.yml', 'r') as f:
            PA_CONFIG = yaml.safe_load( f.read())

    except Exception as e:
        print('CANNOT read pAudio config')
        sys.exit()


def do_refresh():

    def print_things():

        # Visualize from the top of the terminal
        sys.stdout.write(CURSOR_HOME)

        print(f'{Fmt.BOLD}--- pAudio{Fmt.END}')
        print()
        print(f'{Fmt.BOLD}compressor:     {Fmt.END}', not pp[0]["bypassed"])
        print()
        print(f'{Fmt.BOLD}PREAMP (L/R):{Fmt.END}')
        print(f'source_gain:    {source_gain:5.1f}')
        print(f'delay:          {delay:5.1f}')
        print(f'LU_offset:      {lu_offset:5.1f}')
        print(f'balance:        {balance:5.1f}')
        print()
        print(f'{Fmt.BOLD}{lspk} EQ (L/R):{Fmt.END}')
        print(f'{lspk_eq}')
        print()
        print(f'{Fmt.BOLD}DRC{Fmt.END} (gain {drc_gain:5.1f} dB):')
        print('L:', f'{drc_L_numberOfFilters:2d} x', drc_L_typeOfFilters)
        print('R:', f'{drc_R_numberOfFilters:2d} x', drc_R_typeOfFilters)
        print()
        print(f'{Fmt.BOLD}--- CamillaDSP{Fmt.END} {Fmt.ITALIC}(ver: {cdsp_version} lib: {cdsp_lib_version}){Fmt.END}')
        print(f'samplerate:     {samplerate:<6}')
        print(f'buffer:         {chunk_size:4d}')
        print(f'state:          {state:<15}')
        print(f'main volume:    {vol:7.1f}          {muted}')
        print(f'input peak dB:  {level[0]:7.1f} {level[1]:7.1f}')
        print()
        if sys.platform == 'linux':
            print(f'{Fmt.BOLD}--- Jack{Fmt.END} {Fmt.ITALIC}({jack_version}){Fmt.END}')
            print(f'{jack_parameters}')
            print()
        print(f'{Fmt.BOLD}--- System load{Fmt.END}')
        print(f'CPU:         {get_cpu_pcent():4.1f} %')
        print(f'CamillaDSP:  {Fmt.BG_YELLOW}{Fmt.BOLD}{Fmt.BLACK}{load:4.1f} %{Fmt.END}')
        if sys.platform == 'linux':
            print(f'Jack:        {JC.cpu_load():4.1f} % {Fmt.BOLD}{jack_RT}{Fmt.END}')
        print()

        # hide cursor and force the terminal to display the changes immediately
        sys.stdout.write(CURSO_HIDE)
        sys.stdout.flush()


    cdsp_version     = '.'.join(CC.versions.camilladsp())
    cdsp_lib_version = '.'.join(CC.versions.library())

    vol     = CC.volume.main_volume()
    muted   = CC.volume.main_mute()

    state   = CC.general.state().name
    load    = round( CC.status.processing_load(), 1 )

    cc       = CC.config.active()

    chunk_size = cc.get('devices', {}).get('chunksize', 0)
    samplerate = cc.get('devices', {}).get('samplerate', 0)

    if cc.get('devices', {}).get('capture', {}):
        cap_dev = cc['devices']['capture']['device']
    else:
        cap_dev = '--'

    if cc.get('devices', {}).get('playback', {}):
        pbk_dev = cc['devices']['playback']['device']
    else:
        pbk_dev = '--'

    level     = CC.levels.capture_peak()

    # pAudio stuff
    gainL       = cc["filters"]["bal_pol_L"]["parameters"]["gain"]
    gainR       = cc["filters"]["bal_pol_R"]["parameters"]["gain"]
    balance     = - gainL + gainR

    drc_gain    = cc["filters"]["flat_gain_drc"]["parameters"]["gain"]
    lu_offset   = cc["filters"]["lu_offset"]["parameters"]["gain"]
    source_gain = cc["filters"]["source_gain_offset"]["parameters"]["gain"]
    delay       = cc["filters"]["preamp_delay"]["parameters"]["delay"]

    pp = cc["pipeline"]

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


    drc_L_typeOfFilters = get_drc_filters_type( cc, pp[drc_L_step]["names"] )
    drc_R_typeOfFilters = get_drc_filters_type( cc, pp[drc_R_step]["names"] )

    drc_L_numberOfFilters = len(pp[drc_L_step]["names"])
    drc_R_numberOfFilters = len(pp[drc_R_step]["names"])

    if lspk_eq_L_step > 3:
        lspk_eq = pp[lspk_eq_L_step]["names"]
    else:
        lspk_eq = 'n/a'

    muted = f'{Fmt.BOLD}(muted){Fmt.END}' if muted else '       '
    lspk  = PA_CONFIG.get('loudspeaker', 'unknown lspk')

    print_things()


if __name__ == "__main__":

    os.system('cls' if os.name == 'nt' else 'clear')

    get_pa_config()

    CC = CamillaClient("127.0.0.1", 1234)
    CC.connect()

    while True:
        try:
            do_refresh()
            sleep(1)
        except KeyboardInterrupt:
            # restore cursor
            sys.stdout.write(CURSO_SHOW)
            sys.stdout.flush()
            sys.exit()
