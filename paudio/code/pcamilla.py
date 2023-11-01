#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  subprocess as sp
from    time import sleep
import  json
from    camilladsp import CamillaConnection
import  make_eq as me
from    miscel import list_remove_by_pattern


# CamillaDSP needs a new FIR filename in order to
# reload the convolver coeffs
last_eq = 'A'
eq_flat_path = f'../eq/eq_flat.pcm'
eq_A_path = f'../eq/eq_A.pcm'
eq_B_path = f'../eq/eq_B.pcm'
eq_link = '../eq/eq.pcm'
sp.Popen(f'cp {eq_flat_path} {eq_A_path}'.split())
sp.Popen(f'cp {eq_flat_path} {eq_B_path}'.split())


# Starting CamillaDSP (muted)
sp.call("pkill camilladsp".split())
sp.Popen("camilladsp -m -a 127.0.0.1 -p 1234 camilladsp.yml".split())
sleep(1)
PC = CamillaConnection("127.0.0.1", 1234)

PC.connect()

# Initial config snapshot
CFG_INIT = PC.get_config()


# INTERNAL

def set_device(devID):
    cfg = PC.get_config()
    cfg["devices"]["playback"]["device"] = devID
    set_config_sync(cfg)

def set_config_sync(cfg):
    PC.set_config(cfg)
    sleep(.1)


def get_state():
    """ This is the internal camillaDSP state """
    return json.dumps( str( PC.get_state() ) )


def get_config():
    return json.dumps( PC.get_config() )


def get_pipeline():
    return json.dumps( PC.get_config()["pipeline"] )


# Getting AUDIO

def get_drc_sets():
    filters = CFG_INIT["filters"]
    drc_sets = []
    for f in filters:
        if f.startswith('drc'):
            drc_set = f.split('.')[-1]
            if not drc_set in drc_sets:
                drc_sets.append(drc_set)
    return drc_sets


def get_xo_sets():
    return []


def get_drc_gain():
    return json.dumps( PC.get_config()["filters"]["drc_gain"] )


# Setting AUDIO

def reload_eq():

    def toggle_last_eq():
        global last_eq
        last_eq = {'A':'B', 'B':'A'}[last_eq]


    me.make_eq()
    eq_path     = f'../eq/eq_{last_eq}.pcm'
    me.save_eq_IR(eq_path)
    # For convenience, it will be copied to eq.pcm,
    # so that a viewer could display the current curve
    sp.call(f'rm {eq_link}'.split())
    sp.Popen(f'ln -s {eq_path} {eq_link}'.split())
    cfg = PC.get_config()
    cfg["filters"]["eq"]["parameters"]["filename"] = eq_path
    set_config_sync(cfg)
    toggle_last_eq()


def set_mute(mode):
    res = str( PC.set_mute(mode) )
    if res == 'None':
        res = 'done'
    return res


def set_volume(dB):
    res = str( PC.set_volume(dB) )
    if res == 'None':
        res = 'done'
    return res


def set_treble(dB):
    if abs(dB) > 12:
        return 'out of range'
    me.treble  = float(dB)
    reload_eq()
    return 'done'


def set_bass(dB):
    if abs(dB) > 12:
        return 'out of range'
    me.bass  = float(dB)
    reload_eq()
    return 'done'


def set_loudness(mode):
    me.equal_loudness = mode
    reload_eq()
    return 'done'


def set_drc(drcID):

    result = ''

    cfg = PC.get_config()

    if drcID == 'none':
        try:
            for n in (1,2):
                old = cfg["pipeline"][n]['names']
                new = list_remove_by_pattern(old, 'drc.')
                cfg["pipeline"][n]['names'] = new
            set_config_sync(cfg)
            result = 'done'
        except Exception as e:
            result = str(e)

    else:
        try:
            cfg["pipeline"][1]['names'] = CFG_INIT["pipeline"][1]['names']
            cfg["pipeline"][2]['names'] = CFG_INIT["pipeline"][2]['names']
            set_config_sync(cfg)
            result = 'done'
        except Exception as e:
            result = str(e)

    return result


def set_drc_gain(dB):
    cfg = PC.get_config()
    cfg["filters"]["drc_gain"]["parameters"]["gain"] = dB
    set_config_sync(cfg)

