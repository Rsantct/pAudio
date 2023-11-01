#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  yaml
import  os
UHOME = os.path.expanduser('~')
MAINFOLDER = f'{UHOME}/paudio'


def read_user_config():
    with open(f'{MAINFOLDER}/config.yml', 'r') as f:
        c = yaml.safe_load(f.read())
    return c


def read_cmd_phrase(cmd_phrase):
    """
        Command phrase SYNTAX must start with an appropriate prefix:

            preamp  command  arg1 ... [add]
            players command  arg1 ...
            aux     command  arg1 ...

        The 'preamp' prefix can be omited

        The 'add' option for relative level, bass, treble, ...
    """

    pfx, cmd, argstring, add = '', '', '', False

    # This is to avoid empty values when there are more
    # than on space as delimiter inside the cmd_phrase:
    chunks = [x for x in cmd_phrase.split(' ') if x]

    if 'add' in chunks:
        add = True
        chunks.remove('add')

    # If not prefix, will treat as a preamp command kind of
    if not chunks[0] in ('preamp', 'player', 'aux'):
        chunks.insert(0, 'preamp')
    pfx = chunks[0]

    if chunks[1:]:
        cmd = chunks[1]
    if chunks[2:]:
        # <argstring> can be compound
        argstring = ' '.join( chunks[2:] )

    return pfx, cmd, argstring, add


def x2int(x):
    return int(round(float(x)))


def x2float(x):
    return round(float(x),1)


def x2bool(x):
    if x.lower() in ['true', 'on', '1']:
        return True
    elif x.lower() in ['false', 'off', '0']:
        return False
    else:
        return None


def switch(new, curr):
    if new == 'toggle':
        new = {True:False, False:True}[curr]
    else:
        new = x2bool(new)
    return new


def list_remove_by_pattern(l, p):
    l = [x for x in l if p not in x]
    return l

