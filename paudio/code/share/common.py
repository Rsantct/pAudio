#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import  yaml
import  json
from    fmt import Fmt
import  sys
import  os

UHOME = os.path.expanduser('~')
MAINFOLDER      = f'{UHOME}/paudio'
LSPKSFOLDER     = f'{MAINFOLDER}/loudspeakers'
EQFOLDER        = f'{MAINFOLDER}/eq'
CODEFOLDER      = f'{MAINFOLDER}/code'
CONFIG_PATH     = f'{MAINFOLDER}/config.yml'
DSP_LOGFOLDER   = f'{MAINFOLDER}/log'

try:
    os.mkdir(DSP_LOGFOLDER)
except:
    pass

CONFIG = {}


def init():

    global CONFIG

    CONFIG = read_yaml_file(CONFIG_PATH)

    if not "fs" in CONFIG:
        CONFIG["fs"] = 44100
        print('(i) Default to fs=44100')


def get_bit_depth(fmt):
    """ retrieves the bit depth from a given audio sample format,
        e.g. FLOAT32LE, S24LE, ...
    """
    digits = [x for x in fmt if x.isdigit()]
    bd = ''.join(digits)
    return bd


def read_json_file(fpath):
    with open(fpath, 'r') as f:
        d = json.loads(f.read())
    return d


def save_json_file(d, fpath):
    with open(fpath, 'w') as f:
        f.write(json.dumps(d))


def read_yaml_file(fpath):
    with open(fpath, 'r') as f:
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


def get_drc_sets_from_loudspeaker(lspk):
    """ looks for drc.Channel.DrcId.pcm files inside the loudspeaker folder
    """
    drc_files = []
    drc_sets_candidate  = {}
    drc_sets = []

    try:
        files = os.listdir(f'{LSPKSFOLDER}/{lspk}')
        files = [x for x in files if os.path.isfile(f'{LSPKSFOLDER}/{lspk}/{x}') ]
        drc_files = [x for x in files if x.startswith('drc.') ]
    except:
        pass

    for f in drc_files:
        chID  = f.split('.')[1]
        drcID = '.'.join(f.split('.')[2:]).replace('.pcm', '')
        if not drcID in drc_sets_candidate:
            drc_sets_candidate[drcID] = [chID]
        else:
            if not chID in drc_sets_candidate[drcID]:
                drc_sets_candidate[drcID].append(chID)

    for k in drc_sets_candidate:
        channels = drc_sets_candidate[k]
        if sorted(channels) == ['L', 'R']:
            drc_sets.append(k)

    return sorted(drc_sets)


def get_target_sets(fs=44100):
    """ looks for '+x.x-x.x_target_mag.dat files inside the eq folder
    """
    targets_folder  = f'{EQFOLDER}/curves_{fs}_N11/room_target'
    files = []
    sets  = []

    try:
        files = os.listdir(targets_folder)
        files = [x for x in files if os.path.isfile(f'{targets_folder}/{x}') ]
        files = [x for x in files if x.endswith('_target_mag.dat') ]
    except:
        pass

    for file in files:
        tID = file.split('_target')[0]
        if not tID in sets:
            sets.append(tID)

    return sorted(sets)


init()
