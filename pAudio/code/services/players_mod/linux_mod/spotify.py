#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" A Spotify Desktop interface module for players.py
"""

from   subprocess import run as sp_run
import json
import os
import sys
from   pydbus import SessionBus
from   time import sleep

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import  time_sec2hhmmss, Fmt

BUS = SessionBus()


# for testing
def _iterate_spotify_info():
    """ solo para ver lo que hay

    #   === Propiedades de org.mpris.MediaPlayer2.Player ===
    #   PlaybackStatus: Playing | Paused
    #   LoopStatus: None | Playlist | Track
    #   Rate: 1.0
    #   Shuffle: False | True
    #   Metadata: {
            #'mpris:trackid': '/com/spotify/track/5Q0x8J4Pt9uudVST0rZIAv',
            #'mpris:length': 480973000,
            #'mpris:artUrl': 'https://i.scdn.co/image/ab67616d0000b273d52e831a699e7635bcb56c4c',
            #'xesam:album': 'SOURCE',
            #'xesam:albumArtist': ['Nubya Garcia'],
            #'xesam:artist': ['Nubya Garcia'],
            #'xesam:autoRating': 0.13,
            #'xesam:discNumber': 1,
            #'xesam:title': 'Before Us: In Demerara & Caura [Feat. Ms MAURICE]',
            #'xesam:trackNumber': 8,
            #'xesam:url': 'https://open.spotify.com/track/5Q0x8J4Pt9uudVST0rZIAv'
    #   }
    #   Volume: 1.0
    #   Position: 67658000
    #   MinimumRate: 1.0
    #   MaximumRate: 1.0
    #   CanGoNext: True
    #   CanGoPrevious: True
    #   CanPlay: True
    #   CanPause: True
    #   CanSeek: True
    #   CanControl: True

    """

    spotify_path = "/org/mpris/MediaPlayer2"
    spotify_name = "org.mpris.MediaPlayer2.spotify"

    # Obtenemos el objeto completo
    spotify_obj = BUS.get(spotify_name, spotify_path)

    # Obtenemos la interfaz de propiedades
    props = bus.get(spotify_name, spotify_path)["org.freedesktop.DBus.Properties"]

    # Interfaces a inspeccionar
    interfaces = ["org.mpris.MediaPlayer2", "org.mpris.MediaPlayer2.Player"]

    for iface in interfaces:
        print(f"=== Propiedades de {iface} ===")
        all_props = props.GetAll(iface)
        for key, value in all_props.items():
            print(f"{key}: {value}")
        print("\n")


def get_info():

    spotibus = BUS.get("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    metadata = spotibus.Metadata

    info = {
        "player":       "Spotify",
        "state":        spotibus.PlaybackStatus,
        "loop_mode":    spotibus.LoopStatus,
        "shuffle":      spotibus.Shuffle,
        "time_pos":     time_sec2hhmmss( spotibus.Position / 1e6 ),
        "time_tot":     time_sec2hhmmss( metadata.get("mpris:length") / 1e6 ),
        # 2025-11 spotify premium lossless 1411 kbps
        "bitrate":      '1411',
        "format":       '44100:16:2',
        "artist":       '',
        "album":        metadata.get("xesam:album"),
        "title":        metadata.get("xesam:title"),
        "track_num":    metadata.get("xesam:trackNumber"),
        "track_uri":    metadata.get("xesam:url"),
        "tracks_tot":   '',
        "art_url":      metadata.get("mpris:artUrl"),
        "samplerate":   '44100'
    }

    # Example of albumArtist (set of tracks) vs artist (track):
    #
    # "albumArtist":  ['Keith Jarrett']
    # "artist":       ['Samuel Barber'],
    # "album":        "Samuel Barber: Piano Concerto, Op.38 / Béla Bartók: Piano Concerto No.3 / Keith Jarrett: Tokyo Encore (Live)",
    # "url":          "https://open.spotify.com/track/0hbnr74QRhObmbn4FHjvnN",
    #
    # 'artist' changes from ['Samuel Barber'] to ['Béka Bartók']
    # depending on the track throughout the album
    # 'albumArtist' keeps ['Keith Jarret'] on all tracks

    # These are lists
    albumArtist = metadata.get("xesam:albumArtist")
    artist      = metadata.get("xesam:artist")

    tmp = albumArtist + artist
    artists = []
    [artists.append(x) for x in tmp if x not in artists]

    info["artist"] = ' - '.join(artists)

    return info


def playback_control(cmd, arg=''):
    """ Controls the Spotify Desktop player
        input:  a command string
        output: the resulting status string
        (string)
    """
    result = 'not connected'

    spotibus = BUS.get("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")


    # try reconnecting if SessionBus was lost for some reason
    try:
        spotibus.CanControl
    except:
        spotibus_connect()
    if not spotibus:
        return result

    try:
        if   cmd == 'state':
            pass

        elif cmd == 'play':
            spotibus.Play()

        elif cmd == 'pause':
            spotibus.Pause()

        elif cmd == 'next':
            spotibus.Next()

        elif cmd == 'previous':
            spotibus.Previous()

        # MPRIS Shuffle is an only-readable property.
        # (https://specifications.freedesktop.org/mpris-spec/latest/Player_Interface.html)
        elif cmd == 'random':

            if arg in ('get', ''):
                return spotibus.Shuffle

            elif arg in ('on', 'off'):
                set_shuffle(arg)
                return spotibus.Shuffle

            else:
                return f'error with \'random {arg}\''

        elif cmd == 'volume':

            if arg:
                spotibus.Volume = float(arg)

            else:
                return str( round(spotibus.Volume, 2) )


        # MPRIS needs some time to receive the async change from Spotify
        sleep(0.5)
        curr = spotibus.PlaybackStatus
        result = {  'Playing':  'play',
                    'Paused':   'pause',
                    'Stopped':  'stop' } [curr]

    except:
        pass

    return result


if __name__ == "__main__":

    info = get_spotify_info()
    print( json.dumps(info) )
