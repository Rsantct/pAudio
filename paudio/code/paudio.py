#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

from  services import preamp

# This import works because the main program server.py
# is located under the same folder then the commom module
from  common import *


def do(cmd_phrase):

    prefix, cmd, args, add = read_cmd_phrase(cmd_phrase)
    result    = ''

    match prefix:

        case 'preamp':
            result = preamp.do(cmd, args, add)

        # PENDING
        case 'aux':

            match cmd:

                case 'get_web_config':
                    result = json.dumps({   'main_selector':        'inputs',
                                            'LU_monitor_enabled':   True
                                        })

                case 'get_lu_monitor':
                    result = json.dumps(read_json_file(LDMON_PATH))

        # PENDING
        case 'players':
            pass

        case _:
            # This should never occur because preamp is the defaulted as prefix
            result = 'unknown service'

    return result

