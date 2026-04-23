#!/usr/bin/env python3
"""
  Monitor the  CamillaDSP signal level and status,
  or gets the current whole configuration or the pipeline

  Usage:    paudio_camilla_info.py [--config] [--pipeline]
"""

import  os
import  sys
import  yaml
from    time import sleep
import  platform
import  json
from    camilladsp import CamillaClient

UHOME = os.path.expanduser('~')


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

    cap_dev = '- not configured -'
    pbk_dev = '- not configured -'
    chunksize = 0

    config = CC.config.active()

    if config:

        chunk_size = config.get('devices', {}).get('chunksize', 0)
        print('BUFFER:      ', chunk_size)

        if config.get('devices', {}).get('capture', {}):
            cap_dev = config['devices']['capture']['device']
        if config.get('devices', {}).get('playback', {}):
            pbk_dev = config['devices']['playback']['device']

    print('CAPTURE_DEV: ', cap_dev)
    print('PLAYBK_DEV:  ', pbk_dev)
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


def camilladsp_connect():

    try:
        CC.connect()
        CC.disconnect()
        return True

    except Exception as e:
        #print(str(e))
        return False


def load_pAudio_cfg():

    try:
        with open(f'{UHOME}/pAudio/config.yml', 'r') as f:
            return yaml.safe_load( f.read() )

    except:
        return {}


if __name__ == "__main__":

    online = False
    mode = 'monitor'
    for opc in sys.argv[1:]:

        if '-c' in opc:
            mode = 'get_config'

        elif '-p' in opc:
            mode = 'get_pipeline'

        elif '-h' in opc:
            print(__doc__)
            sys.exit()

    PORT  = load_pAudio_cfg().get('camilladsp_port', 1234)

    CC = CamillaClient('127.0.0.1', PORT)

    # not available
    if not camilladsp_connect():
        print('NOT_AVAILABLE')
    else:
        online = True

    # config mode
    if mode in ('get_config', 'get_pipeline'):
        if not online:
            sys.exit()
        CC.connect()
        c = CC.config.active()
        if mode == 'get_config':
            print( json.dumps(c, indent=2) )
        elif mode == 'get_pipeline':
            print( json.dumps(c["pipeline"], indent=2) )
        sys.exit()

    # loop status
    if online:
        print_header()

    while True:

        try:
            print_current()

        except:
            print('NOT_AVAILABLE')

        sleep(1.5)
