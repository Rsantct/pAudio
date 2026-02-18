#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" A MPD interface module for players.py
"""
import  os
import  sys
import  mpd
from    time        import sleep
import  json
from    subprocess  import Popen, run

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import  time_sec2hhmmss, time_sec2mmss, read_mpd_config, \
                    read_json_file, get_pid_cmdline, Fmt,            \
                    PLAYERTEMPLATE, MAINFOLDER, CDDA_META_PATH

MPD_PORT = 6600
CDDA_MPD_PLAYLIST_PATH  = f'{MAINFOLDER}/.cdda_mpd_playlist'
LAST_MPD_PLAYLIST_PATH  = f'{MAINFOLDER}/.last_mpd_playlist'

CLI             = mpd.MPDClient()
CLI.timeout     = 3 # network timeout in seconds (floats allowed), default: None
CLI.idletimeout = 1 # timeout for fetching the result of the idle command is handled seperately, default: None


# NOTE: each command below will do:
#           _ping_mpd()
#           ...somo process...
#           _release_mpd()


def _init():
    global MPD_PORT
    MPD_PORT = read_mpd_config().get('port', 6600)


def read_cdda_meta_from_disk():
    """ wrapper for reading the cdda metadata dict from disk
        (dictionary)
    """

    result = read_json_file( CDDA_META_PATH )

    if not result:
        result = META_TEMPLATE.copy()

    return result


def _ping_mpd():
    """ (i) Do not use ping() because it sometimes crash:
            Got unexpected return value: <...a sringify state...>

        Use status() instead.
    """

    result = False

    try:
        CLI.connect('localhost', MPD_PORT)
        result = True

    except Exception as e:

        if str(e) == "Already connected":
            result = True

        else:
            print(f'{Fmt.BOLD}(mpd_mod.py) ping_mpd: {str(e)}{Fmt.END}')


    return result


def _release_mpd():

    try:
        CLI.close()
        CLI.disconnect()

    except Exception as e:
            print(f'{Fmt.BOLD}(mpd_mod.py) Error disconecting from the MPD server: {str(e)}{Fmt.END}')

    return


def mpd_cdda_in_playlist(all_or_any='any'):

    # to debug the server
    #print(f'{Fmt.MAGENTA}mpd_cdda_in_playlist{Fmt.END}')

    result = False

    if not _ping_mpd():
        print(f'{Fmt.RED}(mpd_mod.py) mpd_cdda_in_playlist not connected to MPD{Fmt.END}')
        return result

    pl = CLI.playlist()

    # example:
    # ['file: cdda://dev/cdrom/1',
    #  'file: cdda://dev/cdrom/2',
    #  'file: cdda://dev/cdrom/3',
    #   ... ]

    if all_or_any == 'any':
        result = any( [ 'cdda:/' in x for x in pl ] )
    else:
        result = all( [ 'cdda:/' in x for x in pl ] )

    _release_mpd()

    return result


def mpd_get_cd_track_nums():
    """ special use for CD
    """

    # to debug the server
    #print(f'{Fmt.MAGENTA}mpd_get_cd_track_nums{Fmt.END}')

    result = []

    if not _ping_mpd():
        print(f'{Fmt.RED}(mpd_mod.py) mpd_get_cd_track_nums not connected to MPD{Fmt.END}')
        return result

    if mpd_cdda_in_playlist('all'):
        result = CLI.playlist()

    # ['file: cdda://dev/cdrom/1',
    #  'file: cdda://dev/cdrom/2',
    #  ... ]

    result = [ x.split('/')[-1] for x in result ]
    # ['1', '2', '3' , ... ]

    _release_mpd()

    return result


def mpd_playlist():

    # to debug the server
    #print(f'{Fmt.MAGENTA}mpd_playlist{Fmt.END}')

    result = []

    if not _ping_mpd():
        print(f'{Fmt.RED}(mpd_mod.py) mpd_playlist not connected to MPD{Fmt.END}')
        return result


    try:
        tmp = CLI.playlistid()

        if mpd_cdda_in_playlist('all'):
            print(f'{Fmt.BLUE}(mpd_mod.py) mpd_playlist is a CD playlist{Fmt.END}')
            result = [ f'{int(x["pos"]) + 1}. {x["name"]}' for x in tmp ]

        else:
            print(f'{Fmt.RED}(mpd_mod.py) mpd_playlist is NOT a CD playlist{Fmt.END}')
            result = [ x["title"] for x in tmp ]

    except Exception as e:
        print(f'{Fmt.RED}(mpd_mod.py) mpd_playlist {str(e)}{Fmt.END}')

    _release_mpd()

    return result


def mpd_playlists(cmd, arg=''):

    # to debug the server
    #print(f'{Fmt.MAGENTA}mpd_playlists{Fmt.END}')


    result = ''

    if not _ping_mpd():
        print(f'{Fmt.RED}(mpd_mod.py) mpd_playlists: not connected to MPD{Fmt.END}')
        return result

    if cmd == 'get_playlists':

        # Some setups could use a mount for mpdconf playlist_directory
        try:
            result = [ x['playlist'] for x in CLI.listplaylists() ]

        # [52@0] {listplaylists} Failed to open /mnt/qnas/media/playlists/: No such file or directory
        except Exception as e:
            print(f'{Fmt.RED}(mpd_mod.py) error with `{cmd}` {str(e)}{Fmt.END}')


    elif cmd == 'load_playlist':

        try:
            CLI.load(arg)
            result = f'ordered loading `{arg}`'
        except Exception as e:
            result = f'{str(e)}'


    elif cmd == 'clear_playlist':

        try:
            CLI.clear()
            sleep(.2)
            result = 'playlist cleared'
        except Exception as e:
            result = f'{str(e)}'


    _release_mpd()

    return result


def playback_control( cmd, arg='', port=MPD_PORT ):
    """ Comuticates to MPD music player daemon

        Input:      a command [arg] to query to the MPD daemon

        Returns:    a playback state string ( stop | play | pause )
                    OR
                    a random mode (on/off)
    """

    # to debug the server
    #print(f'{Fmt.MAGENTA}mpd_control{Fmt.END}')


    if not _ping_mpd():
        print(f'{Fmt.RED}(mpd_mod.py) mpd_control not connected to MPD{Fmt.END}')
        return 'stop'

    # Do execute the command:

    try:
        match cmd:

            case 'state':
                pass

            case 'stop':
                CLI.stop()

            case 'pause':
                CLI.pause()

            case 'play':
                CLI.play()

            case 'play_track':
                CLI.play(int(arg) - 1)

            case 'next':
                CLI.next()

            case 'previous':
                CLI.previous()

            case 'rew_15min':
                CLI.seekcur('-900')

            case 'rew_5min':
                CLI.seekcur('-300')

            case 'rew':
                CLI.seekcur('-30')

            case 'ff':
                CLI.seekcur('+30')

            case 'ff_5min':
                CLI.seekcur('+300')

            case 'ff_15min':
                CLI.seekcur('+900')

            case 'random':

                if arg == 'on':
                    CLI.random(1)

                elif arg == 'off':
                    CLI.random(0)

                elif arg == 'toggle':
                    st = CLI.status()
                    if 'random' in st:
                        CLI.random( {'0':1, '1':0}[ st["random"] ])


    except Exception as e:
        print(f'{Fmt.RED}(mpd_mod.py) error with `{cmd}`{Fmt.END}' )
        print(f'{Fmt.RED}(mpd_mod.py) {str(e)}{Fmt.END}' )


    # After execution, get the new state:

    if cmd == 'random':
        result = 'off'
    else:
        result = 'stop'

    try:
        st = CLI.status()

        try:

            if cmd == 'random':

                result = {'0':'off', '1':'on'}[ st['random'] ]

            else:

                if 'state' in st:
                    result = st['state']

        except Exception as e:
            print(f"{Fmt.RED}(mpd_mod.py) mpd_control {str(e)}{Fmt.END}")

    except Exception as e:
        print(f'{Fmt.RED}(mpd_mod.py) `status` no answer from MPD{Fmt.END}')


    _release_mpd()

    return result


def get_info():
    """ Comuticates to MPD music player daemon
        Return:     player info and track metadata dict
    """

    def get_bitrate_from_format(f):
        """ example '44100:16:2'
        """
        br = ''
        try:
            a,b,c = f.split(':')
            br = round(int(a) * int(b) * int(c) / 1e6, 3)
            br = str(br)
        except Exception as e:
            print(e)
        return br

    pi = PLAYERTEMPLATE.copy()

    pi['player'] = 'MPD'

    if not _ping_mpd():
        print(f'{Fmt.RED}(mpd_mod.py) get_info not connected to MPD{Fmt.END}')
        return  pi

    try:
        st = CLI.status()
        pi["state"] = st.get('state', 'stop')

    except Exception as e:
        print(f'{Fmt.RED}(mpd_mod.py) ERROR getting state: {str(e)}{Fmt.END}')
        return pi

    try:
        cs = CLI.currentsong()

    except Exception as e:
        print(f'{Fmt.RED}(mpd_mod.py) `currentsong` no answer from MPD{Fmt.END}')
        return pi


    # (i) Not all tracks have complete currentsong() fields. Some examples:
    #
    #   {'file': 'http://192.168.1.46:49149/qobuz/track/version/1/trackId/4526528',
    #   'artist': 'Claudio Arrau',
    #   'album': 'Liszt: Piano Sonata in B Minor / Annees De Pelerinage / Ballade No. 2 / Transcendental Etude No. 10 (Arrau) (1970-1981)',
    #   'title': 'Piano Sonata in B Minor, S. 178/R. 21',
    #   'pos': '0',
    #   'id': '135'}
    #
    #   {'file': 'https://rtvelivestream.akamaized.net/rtvesec/rne/GL0/34_2024_07_11_20_11_03_113822.ts',
    #   'pos': '0',
    #   'id': '156'}


    # Skip if no currentsong is loaded
    if cs:
        if 'artist' in cs:
            pi['artist']    = cs['artist']

        if 'album' in cs:
            pi['album']     = cs['album']

        if 'track' in cs:
            pi['track_num'] = cs['track']

        if 'title' in cs:
            pi['title']     = cs['title']
        elif 'file' in cs:
            pi['title']     = cs['file'].split('/')[-1]

        if 'file' in cs:
            pi['file']      = cs["file"]

            if not 'album' in cs:
                # Try to put the URL site as 'album', if available
                if '//' in pi['file']:
                    pi['album'] = '/'.join( pi['file'].split('/')[:3] )


    if 'playlistlength' in st:
        pi['tracks_tot']    = st['playlistlength']

    if 'bitrate' in st:
        # playing wav/aiff/cdda files gives bitrate: '0'
        if st['bitrate'] != '0':
            pi['bitrate']   = st['bitrate']  # kbps

    if 'audio' in st:
        pi['format'] = st['audio']

        if not pi['bitrate']:
            pi['bitrate'] = get_bitrate_from_format( pi['format'] )

    if 'time' in st:
        # time is given as a string 'current:total', each part in seconds

        tmp_pos = time_sec2hhmmss( int( st["time"].split(':')[0] ))
        tmp_tot = time_sec2hhmmss( int( st["time"].split(':')[1] ))

        pi["time_pos"] = tmp_pos
        pi["time_tot"] = tmp_tot


    # Special case CD audio we need to read artist and album
    # from the .cdda_metadata file previously saved to disk
    if 'file' in cs and 'cdda:/' in cs["file"]:

        curr_cd_track =  cs["file"].split('/')[-1]

        cdda_meta = read_cdda_meta_from_disk()

        pi["artist"]    = cdda_meta["artist"]
        pi["album"]     = cdda_meta["album"]
        pi["track_num"] = curr_cd_track
        pi["title"]     = cdda_meta["tracks"][curr_cd_track]["title"]


    _release_mpd()

    return pi


_init()


if __name__ == "__main__":

    if _ping_mpd():
        print(f'Hello. Found MPD version {CLI.mpd_version}. Bye!')

    else:
        print('Cannot connect to MPD')
