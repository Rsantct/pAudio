#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import os
import subprocess as sp
import json
import yaml


# (i) USER CONFIG in the accompanying file  ** macos_players.conf **
# The first one has precedence if more than one are in 'play' state
default_preferred_apps = [
    'Spotify',
    'Music',
    'QuickTime Player',
    'VLC',
    'IINA'
]


# Dict of playback applications and its AppleScript
PLAYERS = {

    "Spotify": '''
        if application "Spotify" is running then
            tell application "Spotify"
                if player state is playing or player state is paused then
                    set tName   to ""
                    set aName   to ""
                    set alName  to ""
                    set tURI    to ""
                    set tNum    to ""
                    try
                        if name of current track is not missing value then set tName to name of current track
                    end try
                    try
                        if artist of current track is not missing value then set aName to artist of current track
                    end try
                    try
                        if album of current track is not missing value then set alName to album of current track
                    end try
                    try
                        if id of current track is not missing value then set tURI to id of current track
                    end try
                    try
                        if track number of current track is not missing value then set tNum to track number of current track
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
                    return "{\\"app\\":\\"Spotify\\",\\"state\\":\\"" & pState & "\\",\\"track_num\\":\\"" & tNum & "\\",\\"track\\":\\"" & tName & "\\",\\"track_uri\\":\\"" & tURI & "\\",\\"artist\\":\\"" & aName & "\\",\\"album\\":\\"" & alName & "\\",\\"elapsed\\":" & (round elapsed) & ",\\"duration\\":" & (round dur) & "}"
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

VOID_PLAYER_INFO = {
    "app":          "",
    "state":        "stop",
    "track":        "",
    "artist":       "",
    "album":        "",
    "elapsed":      0,
    "duration":     0
}


def init():

    global preferred_apps

    fname = __file__.replace('.py', '.conf')
    try:
        with open (fname, 'r') as f:
            c = yaml.safe_load(f)
    except Exception as e:
        print(e)
        c = {}

    preferred_apps = c.get('preferred apps', [])

    if not preferred_apps:
        preferred_apps = default_preferred_apps


# this is a copy from share/common.py
def time_sec2hhmmss(x):
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


def info2paudio_format(info):
    """ simply maps the applescript info dict to pAudio dict format
    """

    fs           = ''
    bitrate      = '-'
    track_format = '-:-:2'

    match info.get('app'):


        case 'Spotify':
            fs = '44100'
            track_format = f'{fs}:16:2'
            # 2025-11 spotify premium lossless
            bitrate = '1411'
            time_tot = time_sec2hhmmss( int(info.get('duration')) / 1000 )

        case _:
            time_tot = time_sec2hhmmss( int(info.get('duration')) )


    res = { 'player':       info.get('app', ''),
            'state':        info.get('state', 'stop'),
            'time_pos':     str( time_sec2hhmmss( int(info.get('elapsed')) ) ),
            'time_tot':     str(time_tot),
            'bitrate':      str(bitrate),
            'artist':       info.get('artist'),
            'album':        info.get('album'),
            'title':        info.get('track'),
            'track_num':    str(info.get('track_num')),
            'track_uri':    info.get('track_uri'),
            'tracks_tot':   '',
            'format':       track_format
            }

    return res


def fix_osascript_info(txt):
    """
        oascript can provide double quotes or other simbols that will not work with json.loads, example:

        {"app":"Spotify",
            "state":"playing",
            "track_num":"4",
            "track":"Piano Sonata No. 17 in D Minor, Op. 31 No. 2 "Tempest": I. Largo - Allegro",
            "track_uri":"spotify:track:5DUmA2IWnnmCOVJM4bIvP3",
            "artist":"Ludwig van Beethoven",
            "album":"Glenn Gould plays Beethoven: Piano Sonatas Nos. 1-3; 5-10; 12-14; 15-18; 23; 30-32",
            "elapsed":24,
            "duration":432826}

        NOTICE
            The above example txt has been splitted manually in lines for readability,
            but it all arrives one after the other without separators

        So we will manually process our matadata fields
    """

    result = {}

    fields = ['"app":', '"state":', '"track_num":', '"track":', '"track_uri":', '"artist":', '"album":', '"elapsed":', '"duration":' ]

    field_indices = []

    for field in fields:

        a = txt.index(field)
        b = a + len(field)

        field_indices.append( (field[1:-2], a, b) )

    for n, i in enumerate(field_indices):


        field = i[0]

        ini = i[2]

        if n  < len(field_indices) - 1:
            end = field_indices[n+1][1] - 1

        else:
            end = -1

        value = txt[ini:end]

        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        # DEBUG
        #print(type(value), f'{field:12}', value)

        result[field] = value

    return result


def run_applescript(script=''):
    """ devuelve una cadena de respuesta
    """

    if not script:
        return None

    tmp = sp.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True
    )

    out = tmp.stdout.strip()
    err = tmp.stderr.strip()

    if out:
        return out

    elif err:
        print(f'(run_applescript) Error: {err}')
        return ''

    else:
        return ''


def get_player_info():
    """ Iterate over preferred_apps
        Return: the app info of the first one found in 'play' state
    """

    players_info = []

    for app in preferred_apps:

        script = PLAYERS[app]

        # run_applescript returns a raw string
        script_ans = run_applescript(script)

        if script_ans:

            try:
                player_info = json.loads(script_ans)

            except Exception as e1:

                try:
                    # Ensure quotation marks, colons, etc are ok for JSON
                    player_info = fix_osascript_info(script_ans)

                except Exception as e:
                    player_info  = VOID_PLAYER_INFO
                    player_info["app"] = app
                    print(f'(players_macos) Error decoding JSON from {app}: {str(e)}')

            if type( player_info ) == dict:
                players_info.append( player_info )

    for player_info in players_info:

        # First app in play state has prececende
        if 'play' in player_info.get('state'):
            break

    if not player_info:
        player_info = {}

    return info2paudio_format(player_info)


init()


if __name__ == "__main__":

    print( json.dumps( get_player_info(), indent=2 ) )
