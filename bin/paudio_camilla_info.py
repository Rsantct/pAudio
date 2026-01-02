#!/usr/bin/env python3
"""
  for testing purposes
"""

import  os
import  sys
from    time import sleep
import  platform
from    camilladsp import CamillaClient


def print_header():

    CC.connect()

    if platform.system() == 'Darwin':

        cap_devs = CC.general.list_capture_devices('CoreAudio')
        cap_devs = [x[0] for x in cap_devs]
        pbk_devs = CC.general.list_playback_devices('CoreAudio')
        pbk_devs = [x[0] for x in pbk_devs]
        print('CAP_DEVICES: ', cap_devs)
        print('PBK_DEVICES: ', pbk_devs)


    state = CC.general.state().name
    print('STATE:       ', state)

    load = round(CC.status.processing_load(), 1)
    print('LOAD:        ', load)

    cap_dev = '--'
    pbk_dev = '--'
    chunksize = 0

    config = CC.config.active()

    if config:

        chunk_size = config.get('devices', {}).get('chunksize', 0)
        print('BUFFER:      ', chunk_size)

        if config.get('devices', {}).get('capture', {}):
            cap_dev = config['devices']['capture']['device']
        if config.get('devices', {}).get('playback', {}):
            pbk_dev = config['devices']['playback']['device']

    print('CAPTURE:     ', cap_dev)
    print('PLAYBACK:    ', pbk_dev)
    print()

    CC.disconnect()


def print_current():

    CC.connect()

    main_volume = CC.volume.main_volume()

    state       = CC.general.state().name

    config      = CC.config.active()

    chunksize   = 0

    if config:
        chunksize = config.get('devices', {}).get('chunksize', 0)

    load        = CC.status.processing_load()

    level       = CC.levels.capture_peak()

    if level:
        level   = [ round(x) for x in level ]
    else:
        level   = ['-', '-']

    print(f'{str(chunksize).rjust(4)} {round(load, 1)} %', f'level: {str(level[0]).rjust(5)} {str(level[1]).rjust(5)} (vol {main_volume})', state)

    CC.disconnect()


def camillacdsp_connect():

    try:
        CC.connect()
        CC.disconnect()
        return True

    except Exception as e:
        #print(str(e))
        return False


if __name__ == "__main__":

    camilladsp_port = 1234

    CC = CamillaClient('127.0.0.1', camilladsp_port)

    if camillacdsp_connect():

        print_header()

    else:
        print('NOT_AVAILABLE')


    while True:

        try:
            print_current()

        except:
            print('NOT_AVAILABLE')

        sleep(1.5)

