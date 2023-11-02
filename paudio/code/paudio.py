#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  preamp
from    miscel import *


def do(cmd_phrase):

    prefix, cmd, args, add = read_cmd_phrase(cmd_phrase)
    result    = ''

    match prefix:

        case 'preamp':
            result = preamp.do(cmd, args, add)

        case 'aux':
            # PENDING
            if cmd == 'get_web_config':
                result = json.dumps({})

        case 'players':
            # PENDING
            pass

        case _:
            # This should never occur because preamp is the default prefix
            result = 'unknown subsystem'


    return result

