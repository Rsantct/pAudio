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


if __name__ == "__main__":


    if cam._connect_to_camilla():

        cap_devs = cam.CC.general.list_capture_devices('CoreAudio')
        cap_devs = [x[0] for x in cap_devs]
        print('CAP_DEVICES: ', cap_devs)

        state = cam.CC.general.state()
        print('STATE:       ', state)

        load = cam.CC.status.processing_load()
        print('LOAD:        ', load)

        config = cam.CC.config.active()
        print('CONFIG:      ', config)


    while True:

        if cam._connect_to_camilla():

            #config = cam.CC.config.active()
            #print('CONFIG:      ', config)
            #
            #state = cam.CC.general.state()
            #print('STATE:       ', state, end='\t')

            level = cam.CC.levels.capture_peak()
            print('level:       ', level)

        else:
            print('NO CONNECTION')

        sleep(1)

