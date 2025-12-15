#!/usr/bin/env python3
"""
  for testing purposes
"""

import  os
import  sys
from    time import sleep

UHOME = os.path.expanduser('~')

sys.path.append(f'{UHOME}/pAudio/code/services/preamp_mod')

import pcamilla as cam
import platform

if __name__ == "__main__":


    if cam._connect_to_camilla():

        if platform.system() == 'Darwin':

            cap_devs = cam.CC.general.list_capture_devices('CoreAudio')
            cap_devs = [x[0] for x in cap_devs]
            pbk_devs = cam.CC.general.list_playback_devices('CoreAudio')
            pbk_devs = [x[0] for x in pbk_devs]
            print('CAP_DEVICES: ', cap_devs)
            print('PBK_DEVICES: ', pbk_devs)


        state = cam.CC.general.state().name
        print('STATE:       ', state)

        load = round(cam.CC.status.processing_load(), 1)
        print('LOAD:        ', load)

        cap_dev = '--'
        pbk_dev = '--'
        chunksize = 0

        config = cam.CC.config.active()

        if config:

            chunk_size = config.get('devices', {}).get('chunksize', 0)
            print('BUFFER:      ', chunk_size)

            if config.get('devices', {}).get('capture', {}):
                cap_dev = config['devices']['capture']['device']
            if config.get('devices', {}).get('playback', {}):
                pbk_dev = config['devices']['playback']['device']

        print('CAPTURE:     ', cap_dev)
        print('PLAYBACK:    ', pbk_dev)


    while True:

        if cam._connect_to_camilla():
            main_volume = cam.CC.volume.main_volume()
            state       = cam.CC.general.state().name
            config      = cam.CC.config.active()
            chunksize   = 0
            if config:
                chunksize = config.get('devices', {}).get('chunksize', 0)
            load        = cam.CC.status.processing_load()
            level       = cam.CC.levels.capture_peak()
            level       = [ round(x, 1) for x in level ]
            print(f'{str(chunksize).rjust(4)} {round(load, 1)} %', f'L{level}R | vol: {main_volume}', state)

        else:
            print('NO CONNECTION')

        sleep(1)

