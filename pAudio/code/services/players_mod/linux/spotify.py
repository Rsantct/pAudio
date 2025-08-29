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

BUS = SessionBus()


# for testing
def _iterate_spotify_info():
    """ solo para ver lo que hay
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


def _time_sec2hhmmss(x):
    """ Format a given float (seconds) to "hh:mm:ss"
        (string)
    """

    if type(x) != float or type(x) != int:
        try:
            x = float(x)
        except:
            x = 0.0

    h = int( x / 3600 )         # hours
    x = int( round(x % 3600) )  # updating x to reamining seconds
    m = int( x / 60 )           # minutes from the new x
    s = int( round(x % 60) )    # and seconds
    return f'{h:0>2}:{m:0>2}:{s:0>2}'


def get_spotify_info():

    spotify = BUS.get("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    metadata = spotify.Metadata

    info = {
        "player":       "Spotify",
        "state":        spotify.PlaybackStatus,
        "loop_mode":    spotify.LoopStatus,
        "shuffle":      spotify.Shuffle,
        "time_pos":     _time_sec2hhmmss( spotify.Position / 1e6 ),
        "time_tot":     _time_sec2hhmmss( metadata.get("mpris:length") / 1e6 ),
        "bitrate":      '320 Kbps',
        "artist":       metadata.get("xesam:albumArtist"),
        "album":        metadata.get("xesam:album"),
        "title":        metadata.get("xesam:title"),
        "track_num":    metadata.get("xesam:trackNumber"),
        "track_uri":    metadata.get("xesam:url"),
        "tracks_tot":   '',
        "art_url":      metadata.get("mpris:artUrl"),
        "samplerate":   '44100'
    }

    artist = info.get('artist')

    if type(artist) == list:
        if len(artist) > 1:
            info["artist"] = ', '.join(artist)
        else:
            info["artist"] = artist[0]
    else:
        try:
            info["artist"] = str( info["artist"] )
        except:
            pass

    return info


if __name__ == "__main__":

    info = get_spotify_info()
    print( json.dumps(info) )
