#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.


""" A module for players.py to deal with Mplayer
"""

# (i) I/O FILES MANAGED HERE:
#
# .{service}_fifo   'w'     Mplayer command input fifo,
#                           (remember to end commands with \n)
# .{service}_events 'r'     Mplayer info output is redirected here
#

from    time import sleep
import  os
import  sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import  MAINFOLDER, PLAYERTEMPLATE, time_sec2hhmmss, \
                    read_last_lines, process_is_running


def playing_status(service='dvb'):
    """ Retrieves Mplayer status: play, pause, n/a
    """
    if not service:
        return 'n/a'

    result = 'play'

    # Avoid writing to a FIFO if mplayer was not working for some reason
    if not process_is_running(f'{service}_fifo'):
        return 'n/a'

    with open(f'{MAINFOLDER}/.{service}_fifo', 'w') as f:
        f.write( 'pausing_keep_force get_property pause\n' )

    last_lines = read_last_lines( f'{MAINFOLDER}/.{service}_events', nlines=5)
    # The result will be based on the last 'ANS_pause' read line
    for line in last_lines:
        if line == 'ANS_pause=yes':
            result = 'pause'
        elif line == 'ANS_pause=no':
            result = 'play'

    return result


def send_mplayer_cmd(cmd, service='dvb'):
    """ Send Mplayer commands through by the corresponding fifo
    """
    # Avoid writing to a FIFO if mplayer was not working for some reason
    if not process_is_running(f'{service}_fifo'):
        return

    with open(f'{MAINFOLDER}/.{service}_fifo', 'w') as f:
        f.write( f'{cmd}\n' )

    if cmd == 'stop':
        # Mplayer needs a while to report the actual state ANS_pause=yes
        sleep(2)


def playback_control(cmd, arg='', service='dvb'):
    """ Sends a command to Mplayer trough by its input fifo
        input:  a command string
        result: a result string: 'play' | 'stop' | 'pause' | ''
    """

    supported_commands = (  'state',
                            'stop',
                            'pause',
                            'play',
                            'next',
                            'previous',
                            'rew',
                            'ff',
                            'play_track',
                            'eject'
                          )

    # (i) The pe.audio.sys plugin redirects Mplayer stdout & stderr
    #     towards special files:
    #       ~/pe.audio.sys/.<service>_events
    #     so that will capture there the Mplayer's answers when
    #     a Mplayer command has been issued.
    #     Available commands: http://www.mplayerhq.hu/DOCS/tech/slave.txt

    status = playing_status(service)

    # Early return if SLAVE GETTING INFO commands:
    if cmd.startswith('get_'):
        send_mplayer_cmd( cmd, service )
        return status

    # Early return if STATE or NOT SUPPORTED command:
    elif cmd == 'state'or cmd not in supported_commands:
        return status

    # Processing ACTION commands (playback control)
    if service == 'istreams':

        # useful when playing a mp3 stream (e.g. a podcast url)
        if   cmd == 'previous':   cmd = 'seek -300 0'
        elif cmd == 'rew':        cmd = 'seek -60  0'
        elif cmd == 'ff':         cmd = 'seek +60  0'
        elif cmd == 'next':       cmd = 'seek +300 0'

        send_mplayer_cmd(cmd, service)

    elif service == 'dvb':

        # (i) all this stuff is testing and not much useful
        if   cmd == 'previous':   cmd = 'tv_step_channel previous'
        elif cmd == 'rew':        cmd = 'seek_chapter -1 0'
        elif cmd == 'ff':         cmd = 'seek_chapter +1 0'
        elif cmd == 'next':       cmd = 'tv_step_channel next'

        send_mplayer_cmd(cmd, service)

    else:
        print( f'(mplayer) unknown Mplayer service \'{service}\'' )

    return status


def get_info(service='dvb'):
    """ gets playing info and metadata from Mplayer as per
        http://www.mplayerhq.hu/DOCS/tech/slave.txt

        input:      service:    dvb | istreams

        output:     the updated player info dict
    """

    pi = PLAYERTEMPLATE.copy()

    pi['player'] = 'Mplayer'

    # This is the file were Mplayer standard output has been redirected to,
    # so we can read there any answer when required to Mplayer slave daemon:
    mplayer_redirection_path = f'{MAINFOLDER}/.{service}_events'

    # Communicates to Mplayer trough by its input fifo
    # to get the current media filename and bitrate:

    mplayer_control(cmd='get_audio_samples', service=service)   # ANS_AUDIO_SAMPLES='48000 Hz, 2 ch.'
    mplayer_control(cmd='get_audio_codec',   service=service)   # ANS_AUDIO_CODEC='ffac3'
    mplayer_control(cmd='get_audio_bitrate', service=service)   # ANS_AUDIO_BITRATE='160 kbps'
    mplayer_control(cmd='get_file_name',     service=service)   # ANS_FILENAME='Radio Clasica HQ'
    mplayer_control(cmd='get_time_pos',      service=service)   # ANS_TIME_POSITION=3840.1
    mplayer_control(cmd='get_time_length',   service=service)   # ANS_LENGTH=-1.24

    # Triyng to read Mplayer output from its redirected file
    lines = []
    tries = 3
    while tries:
        # Waiting for Mplayer ANS_xxxx to be written to the output file
        sleep(.10)
        try:
            # Reading a tail of 350 bytes from the Mplayer output file
            fsize = os.path.getsize(mplayer_redirection_path)
            tail_len = 350
            with open(mplayer_redirection_path, 'rb') as f:
                f.seek(fsize - tail_len)
                lines = f.read(tail_len).decode().split('\n')
            break
        except:
            tries -= 1

    # Reading metadata (will take the last valid field if found in lines)
    #   Some sample lines:
    #       ANS_FILENAME='Radio 3 HQ'
    #       ANS_pause=no
    #       ANS_TIME_POSITION=4399.8
    #       ANS_LENGTH=-0.95
    #       ANS_AUDIO_BITRATE='256 kbps'
    #       ANS_AUDIO_SAMPLES='48000 Hz, 2 ch.'
    for line in lines:

        if 'ANS_AUDIO_CODEC=' in line:
            pi['codec'] = line.split('=')[-1].replace("'", "")

        if 'ANS_AUDIO_SAMPLES=' in line:
            Hz = line.split('=')[-1].replace("'", "").split('Hz')[0]
            ch = line.split('=')[-1].replace("'", "").split('ch')[0].split()[-1]
            pi['format'] = f'{Hz}:-:{ch}'

        if 'ANS_AUDIO_BITRATE=' in line:
            pi['bitrate'] = line.split('=')[-1].replace("'", "").split()[0]

        if 'ANS_FILENAME=' in line:
            pi['title'] = line.split('=')[-1].replace("'", "")

    return pi
