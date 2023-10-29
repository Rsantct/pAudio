#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez


def read_cmd_phrase(c):
    """ Read a command phrase, extracting:
            - command
            - arguments
            - the 'add' option for relative level, bass, treble, ...
    """
    c = c.split(' ')
    if 'add' in c:
        add = True
        c.remove('add')
    else:
        add = False
    cmd = c[0]
    args = ' '.join(c[1:])
    return cmd, args, add


def x2int(x):
    return int(round(float(x)))


def x2float(x):
    return round(float(x),1)

def x2bool(x, curr=False):
    if x.lower() == 'toggle':
        return {True:False, False:True}[curr]
    elif x.lower() in ['true', 'on', '1']:
        return True
    else:
        return False

