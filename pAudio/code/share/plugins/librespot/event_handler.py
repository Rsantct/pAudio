#!/usr/bin/python3
"""
    https://github.com/librespot-org/librespot/blob/dev/contrib/event_handler_example.py
"""
import os
import json
from   datetime import datetime

UHOME       = os.path.expanduser('~')
EVENTS_PATH = f'{UHOME}/pAudio/log/librespot_events'

player_event = os.getenv('PLAYER_EVENT')

d = {
   'event_time': str(datetime.now()),
   'event': player_event,
}


match player_event:

    case 'session_connected' | 'session_disconnected':
        d['user_name']          = os.environ['USER_NAME']
        d['connection_id']      = os.environ['CONNECTION_ID']

    case 'session_client_changed':
        d['client_id']          = os.environ['CLIENT_ID']
        d['client_name']        = os.environ['CLIENT_NAME']
        d['client_brand_name']  = os.environ['CLIENT_BRAND_NAME']
        d['client_model_name']  = os.environ['CLIENT_MODEL_NAME']

    case 'shuffle_changed':
        d['shuffle']            = os.environ['SHUFFLE']

    case 'repeat_changed':
        d['repeat']             = os.environ['REPEAT']

    case 'auto_play_changed':
        d['auto_play']          = os.environ['AUTO_PLAY']

    case 'filter_explicit_content_changed':
        d['filter']             = os.environ['FILTER']

    case 'volume_changed':
        d['volume']             = os.environ['VOLUME']

    case 'seeked' | 'position_correction' | 'playing' | 'paused':
        d['track_id']           = os.environ['TRACK_ID']
        d['position_ms']        = os.environ['POSITION_MS']

    case 'unavailable' | 'end_of_track' | 'preload_next' | 'preloading' | 'loading' | 'stopped':
        d['track_id'] = os.environ['TRACK_ID']

    case 'track_changed':

        common_metadata_fields = {}

        item_type = os.environ['ITEM_TYPE']

        common_metadata_fields['item_type']     = item_type
        common_metadata_fields['track_id']      = os.environ['TRACK_ID']
        common_metadata_fields['uri']           = os.environ['URI']
        common_metadata_fields['name']          = os.environ['NAME']
        common_metadata_fields['duration_ms']   = os.environ['DURATION_MS']
        common_metadata_fields['is_explicit']   = os.environ['IS_EXPLICIT']
        common_metadata_fields['language']      = os.environ['LANGUAGE'].split('\n')
        common_metadata_fields['covers']        = os.environ['COVERS'].split('\n')

        d['common_metadata_fields'] = common_metadata_fields

        if item_type == 'Track':

            track_metadata_fields = {}

            track_metadata_fields['number']         = os.environ['NUMBER']
            track_metadata_fields['disc_number']    = os.environ['DISC_NUMBER']
            track_metadata_fields['popularity']     = os.environ['POPULARITY']
            track_metadata_fields['album']          = os.environ['ALBUM']
            track_metadata_fields['artists']        = os.environ['ARTISTS'].split('\n')
            track_metadata_fields['album_artists']  = os.environ['ALBUM_ARTISTS'].split('\n')

            d['track_metadata_fields'] = track_metadata_fields

        elif item_type == 'Episode':

            episode_metadata_fields = {}

            episode_metadata_fields['show_name']    = os.environ['SHOW_NAME']
            publish_time = datetime.utcfromtimestamp(int(os.environ['PUBLISH_TIME'])).strftime('%Y-%m-%d')
            episode_metadata_fields['publish_time'] = publish_time
            episode_metadata_fields['description']  = os.environ['DESCRIPTION']

            d['episode_metadata_fields'] = episode_metadata_fields


tmp = json.dumps(d)

with open(EVENTS_PATH, 'a') as f:
    f.write(tmp + '\n')
