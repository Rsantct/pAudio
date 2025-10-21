#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    A pAudio daemon to auto eject a CD-Audio when playback is over

    Usage:  auteject_cdda.py  start | stop  &

    (needs:  udisks2, usbmount)
"""

from    os.path import expanduser
import  sys
import  threading
from    time import sleep, ctime
from    subprocess import Popen, call

UHOME = expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from    common  import  read_state_from_disk, read_metadata_from_disk, \
                        time_diff, get_timestamp, LOGFOLDER, USER, CONFIG


def get_cdda_device():
    try:
        with open(f'{UHOME}/pAudio/.cdda_device', 'r') as f:
            return f.read()
    except:
        print(f'{Fmt.MAGENTA}(autoeject_cdda) Using default \'/dev/cdrom\'{Fmt.END}')
        return '/dev/cdrom'


def main_loop():

    def eject_job(timer=3):
        """ Runs forever every <timer> sec: reads the playback files
            to detect when a CD disc is over, then ejects the disc.
        """

        disc_is_over    = False

        while True:

            if not read_state_from_disk().get('source').lower() == 'cd':
                sleep(timer)
                continue

            md = read_metadata_from_disk()
            if not md:
                sleep(timer)
                continue


            track_num = md["track_num"]    # '2'
            tracks    = md["tracks_tot"]   # '6'
            time_pos  = md["time_pos"]     # '01:23'
            time_tot  = md["time_tot"]     # '12:34'

            if time_tot[-2:].isdigit() and time_tot != '00:00' \
               and track_num == tracks:

                diff = time_diff(time_pos, time_tot)
                if type(diff) != str:
                    if abs( diff ) < 4.0:
                        disc_is_over = True

            if disc_is_over:

                tmp = f'{get_timestamp()} tpos: {time_pos.rjust(8)}, ttot: {time_tot.rjust(8)}, track {track_num} of {tracks}'
                print(f'(autoeject_cdda) {tmp}')
                with open(LOG_PATH, 'a') as f:
                    f.write(f'{tmp}, ejecting disc.\n')

                # real audio can be buffered several seconds
                sleep(10)

                cdda_device = get_cdda_device()
                Popen(f"eject {cdda_device}".split())
                print(f'(autoeject_cdda) CD playback is over, disc ejected: {cdda_device}.')
                disc_is_over = False

            sleep(timer)


    job_loop = threading.Thread( target=eject_job, args=() )
    job_loop.start()


def stop():
    call( ['pkill', '-u', USER, '-KILL', '-f', 'autoeject_cdda.py start'] )


if __name__ == '__main__':

    LOG_PATH = f'{LOGFOLDER}/autoeject_cdda.log'



    if sys.argv[1:]:
        if sys.argv[1] == 'start':
            main_loop()
        elif sys.argv[1] == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
