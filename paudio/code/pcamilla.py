#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  subprocess as sp
from    time import sleep
import  json
from    camilladsp import CamillaConnection
import  make_eq as me

# DRC FIRs LEVEL OFFSET
DRC_OFFSET_DB = -5

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
sp.Popen("camilladsp -m -a 127.0.0.1 -p 1234 paudio.yml".split())
sleep(1)
PC = CamillaConnection("127.0.0.1", 1234)
PC.connect()
CFG0 = PC.get_config()


def toggle_last_eq():
    global last_eq
    last_eq = {'A':'B', 'B':'A'}[last_eq]


def reload_eq():
    me.make_eq()
    eq_path     = f'../eq/eq_{last_eq}.pcm'
    me.save_eq_IR(eq_path)
    # For convenience, it will be copied to eq.pcm,
    # so that a viewer could display the current curve
    sp.call(f'rm {eq_link}'.split())
    sp.Popen(f'ln -s {eq_path} {eq_link}'.split())
    cfg = PC.get_config()
    cfg["filters"]["eq"]["parameters"]["filename"] = eq_path
    PC.set_config(cfg)
    toggle_last_eq()


def get_state():
    """ This is the internal camillaDSP state """
    return json.dumps( str( PC.get_state() ) )


def set_mute(mode):
    res = str( PC.set_mute(mode) )
    if res == 'None':
        res = 'done'
    return res


def set_level(dB):
    me.spl = me.LOUDNESS_REF_LEVEL + dB
    reload_eq()
    PC.set_volume(dB)
    return 'done'


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


def get_inputs():
    return []


def get_xo_sets():
    return []


def get_drc_sets():
    filters = CFG0["filters"]
    drc_sets = []
    for f in filters:
        if f.startswith('drc'):
            drc_set = f.split('.')[-1]
            if not drc_set in drc_sets:
                drc_sets.append(drc_set)
    return drc_sets


def set_drc(drcID):

    result = ''

    cfg = PC.get_config()

    if drcID == 'none':
        cfg["pipeline"][1]['names'] = ['eq', 'vol']
        cfg["pipeline"][2]['names'] = ['eq', 'vol']
        PC.set_config(cfg)
        v = PC.get_volume() + DRC_OFFSET_DB
        PC.set_volume(v)
        result = 'done'

    else:
        try:
            cfg["pipeline"][1]['names'] = ['eq', f'drc.L.{drcID}', 'vol']
            cfg["pipeline"][2]['names'] = ['eq', f'drc.R.{drcID}', 'vol']
            PC.set_config(cfg)
            v = PC.get_volume() - DRC_OFFSET_DB
            PC.set_volume(v)
            result = 'done'
        except Exception as e:
            result = str(e)

    return result

