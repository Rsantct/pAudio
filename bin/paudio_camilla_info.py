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

        state = cam.CC.general.state()
        print('STATE:       ', state)

        load = cam.CC.status.processing_load()
        print('LOAD:        ', load)

        config = cam.CC.config.active()
        cap_dev = '--'
        pbk_dev = '--'

        if config:
            if config.get('devices', {}).get('capture', {}):
                cap_dev = config['devices']['capture']['device']
            if config.get('devices', {}).get('playback', {}):
                pbk_dev = config['devices']['playback']['device']

        print('CAPTURE:     ', cap_dev)
        print('PLAYBACK:    ', pbk_dev)


    while True:

        if cam._connect_to_camilla():
            level = cam.CC.levels.capture_peak()
            main_volume = cam.CC.volume.main_volume()
            state = cam.CC.general.state()
            print('level:       ', level, f'main_volume: {main_volume}', f'state: {state}')

        else:
            print('NO CONNECTION')

        sleep(1)

