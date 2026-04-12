#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

from   subprocess   import run as sp_run
from   time         import sleep
import json
import os
import sys

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import  json_string_fix, save_json_file, time_sec2hhmmss, \
                    read_json_file, PLAYER_INFO_PATH

# List of players to be queried so that the response will be faster.
# Set void to query all in _PLAYERS
PLAYERS_OF_INTEREST=['Spotify', 'Music']

# Diccionario de reproductores y su AppleScript, en ORDEN PREFERIDO
_PLAYERS = {

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

def loop_save_player_info(source=''):
    """ This must be threaded
        Will loop every second
        source management is PENDING
    """

    while True:

        player_info = get_player_info()

        for k in 'time_pos', 'time_tot':
            if len(player_info.get(k, '')) > 5 and  player_info.get(k, '').startswith('00:'):
                player_info[k] = player_info[k][3:]

        save_json_file(player_info, PLAYER_INFO_PATH, timeout=0.5)

        sleep(1)


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

    fs           = ''
    bitrate      = '-'
    track_format = '-:-:2'

    match info.get('app'):


        case 'Spotify':
            fs = '44100'
            track_format = f'{fs}:16:2'
            # 2025-11 spotify premium lossless
            bitrate = '1411'
            time_tot = time_sec2hhmmss( info.get('duration') / 1000 )

        case _:
            time_tot = time_sec2hhmmss( info.get('duration') )


    res = { 'player':       info.get('app', ''),
            'state':        info.get('state', 'stop'),
            'time_pos':     time_sec2hhmmss( info.get('elapsed') ),
            'time_tot':     time_tot,
            'bitrate':      bitrate,
            'artist':       info.get('artist'),
            'album':        info.get('album'),
            'title':        info.get('track'),
            'track_num':    info.get('track_num'),
            'track_uri':    info.get('track_uri'),
            'tracks_tot':   '',
            'format':       track_format
            }

    return res


def get_player_info():
    """
    """

    player_info  = {}

    players_info = []

    for player, script in _PLAYERS.items():

        if PLAYERS_OF_INTEREST and not player in PLAYERS_OF_INTEREST:
            continue

        player_info = _run_applescript(script, who=player)


        if player_info:

            try:
                player_info = json.loads(player_info)

            except Exception as e1:

                try:
                    # comillas, dos puntos, etc estén bien formateadas para JSON
                    player_info = json_string_fix(player_info)
                    player_info = json.loads(player_info)

                except Exception as e:
                    print(f'(players_macos) Error decoding JSON from {player}: {str(e)}')

            if type( player_info ) == dict:
                players_info.append( player_info )


    # Orden inverso para quedarnos con el primero de los preferidos
    for player_info in players_info[::-1]:

        if 'play' in player_info.get('state'):
            break

    if player_info:
        return _info2paudio_metadata(player_info)
    else:
        return _info2paudio_metadata(VOID_PLAYER_INFO)


def playback_control(cmd):
    """
    #   Para UN player determinado
    #       tell application "Spotify"
    #           play            -- Reanuda
    #           pause           -- Pausa
    #           playpause       -- Alterna
    #           next track      -- Siguiente
    #           previous track  -- Anterior
    #       end tell
    #
    #   Para simular las Teclas Multimedia para el player de turno
    #       tell application "System Events"
    #           key code 16 -- Play/Pause
    #           key code 17 -- Next
    #           key code 15 -- Previous
    #       end tell
    """

    player = read_json_file(PLAYER_INFO_PATH).get('player', '')

    if not player or player.lower == 'none':
        return 'n/a'

    pbk_script = f'''
        tell application "{player}"
            {cmd}
        end tell
    '''

    _run_applescript(pbk_script)

    return 'ordered'


if __name__ == "__main__":

    print( json.dumps( get_player_info(), indent=2 ) )
