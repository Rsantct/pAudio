#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

from   subprocess import run as sp_run
import json
import os
import sys


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


VOID_PLAYER_INFO = {
    "app":          "",
    "state":        "stop",
    "track":        "",
    "artist":       "",
    "album":        "",
    "elapsed":      0,
    "duration":     0
}


# Diccionario de reproductores y su AppleScript, en ORDEN PREFERIDO
_PLAYERS = {

    "Spotify": '''
        if application "Spotify" is running then
            tell application "Spotify"
                if player state is playing or player state is paused then
                    set tName to ""
                    set aName to ""
                    set alName to ""
                    try
                        if name of current track is not missing value then set tName to name of current track
                    end try
                    try
                        if artist of current track is not missing value then set aName to artist of current track
                    end try
                    try
                        if album of current track is not missing value then set alName to album of current track
                    end try
                    set pState to player state
                    try
                        if player position is not missing value then
                            set elapsed to player position
                        else
                            set elapsed to 0
                        end if
                    on error
                        set elapsed to 0
                    end try
                    try
                        if duration of current track is not missing value then
                            set dur to duration of current track
                        else
                            set dur to 0
                        end if
                    on error
                        set dur to 0
                    end try
                    return "{\\"app\\":\\"Spotify\\",\\"state\\":\\"" & pState & "\\",\\"track\\":\\"" & tName & "\\",\\"artist\\":\\"" & aName & "\\",\\"album\\":\\"" & alName & "\\",\\"elapsed\\":" & (round elapsed) & ",\\"duration\\":" & (round dur) & "}"
                end if
            end tell
        end if
    ''',

    "Music": '''
        if application "Music" is running then
            tell application "Music"
                if player state is playing or player state is paused then
                    set tName to ""
                    set aName to ""
                    set alName to ""
                    try
                        if name of current track is not missing value then set tName to name of current track
                    end try
                    try
                        if artist of current track is not missing value then set aName to artist of current track
                    end try
                    try
                        if album of current track is not missing value then set alName to album of current track
                    end try
                    set pState to player state
                    try
                        if player position is not missing value then
                            set elapsed to player position
                        else
                            set elapsed to 0
                        end if
                    on error
                        set elapsed to 0
                    end try
                    try
                        if duration of current track is not missing value then
                            set dur to duration of current track
                        else
                            set dur to 0
                        end if
                    on error
                        set dur to 0
                    end try
                    return "{\\"app\\":\\"Music\\",\\"state\\":\\"" & pState & "\\",\\"track\\":\\"" & tName & "\\",\\"artist\\":\\"" & aName & "\\",\\"album\\":\\"" & alName & "\\",\\"elapsed\\":" & (round elapsed) & ",\\"duration\\":" & (round dur) & "}"
                end if
            end tell
        end if
    ''',

    # En el resto de players solo nos interesa si están playing,
    # no nos interesa si están paused ya que no los usamos como una gramola

    "QuickTime Player": '''
        if application "QuickTime Player" is running then
            tell application "QuickTime Player"
                if (exists document 1) then
                    if playing of document 1 is true then
                        set playerState to "playing"
                        set movieName to ""
                        try
                            set movieName to name of document 1
                        end try
                        try
                            set elapsed to current time of document 1
                        on error
                            set elapsed to 0
                        end try
                        try
                            set dur to duration of document 1
                        on error
                            set dur to 0
                        end try
                        return "{" & quote & "app" & quote & ":" & quote & "QuickTime Player" & quote & "," & quote & "state" & quote & ":" & quote & playerState & quote & "," & quote & "track" & quote & ":" & quote & movieName & quote & "," & quote & "artist" & quote & ":" & quote & quote & "," & quote & "album" & quote & ":" & quote & quote & "," & quote & "elapsed" & quote & ":" & (round elapsed) & "," & quote & "duration" & quote & ":" & (round dur) & "}"
                    end if
                end if
            end tell
        end if
    ''',

    "VLC": '''
        if application "VLC" is running then
            tell application "VLC"
                if playing then
                    set playerState to "playing"
                    set movieName to ""
                    try
                        set movieName to name of current item
                    end try

                    try
                        set elapsed to current time

                    on error
                        try
                            set elapsed to round (current time)

                        on error
                            set elapsed to 0

                        end try
                    end try

                    try
                        set dur to duration of current item

                    on error
                        try
                            set dur to round (duration of current item)

                        on error
                            try
                                set dur to duration

                            on error
                                set dur to 0

                            end try
                        end try
                    end try

                    return "{\\"app\\":\\"VLC\\",\\"state\\":\\"" & playerState & "\\",\\"track\\":\\"" & movieName & "\\",\\"artist\\":\\"\\",\\"album\\":\\"\\",\\"elapsed\\":" & elapsed & ",\\"duration\\":" & dur & "}"
                end if
            end tell
        end if
    ''',

    "IINA": '''
        if application "IINA" is running then
            tell application "IINA"
                if is playing then
                    set tName to ""
                    set aName to ""
                    set alName to ""
                    try
                        set tName to name of current item
                    end try
                    try
                        set aName to artist of current item
                    end try
                    try
                        set alName to album of current item
                    end try
                    set pState to "playing"
                    try
                        set elapsed to position
                    on error
                        set elapsed to 0
                    end try
                    try
                        set dur to length of current item
                    on error
                        set dur to 0
                    end try
                    return "{\\"app\\":\\"IINA\\",\\"state\\":\\"" & pState & "\\",\\"track\\":\\"" & tName & "\\",\\"artist\\":\\"" & aName & "\\",\\"album\\":\\"" & alName & "\\",\\"elapsed\\":" & (round elapsed) & ",\\"duration\\":" & (round dur) & "}"
                end if
            end tell
        end if
    '''
}


def _run_applescript(script='', who=''):
    """ devuelve una cadena JSON o None
    """

    if not script:
        return None

    tmp = sp_run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True
    )

    out = tmp.stdout.strip()
    err = tmp.stderr.strip()

    if out:
        return out

    elif err:
        #print(f'(players_macos) [{who}] Error applescript: {err}')
        return None

    else:
        return None


def _info2paudio_metadata(info):
    """ simply maps the applescript info dict to pAudio metatdata dict format
    """

    match info.get('app'):

        case 'Spotify':
            fs = '44100'
            time_tot = _time_sec2hhmmss( info.get('duration') / 1000 )

        case _:
            fs = ''
            time_tot = _time_sec2hhmmss( info.get('duration') )


    res = { "player":       info.get('app', ''),
            "state":        info.get('state', 'stop'),
            "time_pos":     _time_sec2hhmmss( info.get('elapsed') ),
            "time_tot":     time_tot,
            "bitrate":      fs,
            "artist":       info.get('artist'),
            "album":        info.get('album'),
            "title":        info.get('track'),
            "track_num":    '',
            "track_uri":    '',
            "tracks_tot":   ''
            }

    return res


def get_player_info( players_of_interest=['Spotify', 'Music'] ):
    """ players_of_interest:    list of players to be queried
                                so that the response will be faster

                                void to query all in _PLAYERS
    """

    player_info  = {}

    players_info = []

    for player, script in _PLAYERS.items():

        if players_of_interest and not player in players_of_interest:
            continue

        player_info = _run_applescript(script, who=player)

        if player_info:

            # comillas estén bien formateadas para JSON
            player_info = player_info.replace('\\"', '"')

            try:
                player_info = json.loads(player_info)
                players_info.append( player_info )

            except Exception as e:
                print(f'(players_macos) Error decoding JSON from {app}: {str(e)}')

    # Orden inverso para quedarnos con el primero de los preferidos
    for player_info in players_info[::-1]:

        if 'play' in player_info.get('state'):
            break

    if player_info:
        return _info2paudio_metadata(player_info)
    else:
        return _info2paudio_metadata(VOID_PLAYER_INFO)


if __name__ == "__main__":

    print( json.dumps( get_player_info() ) )
