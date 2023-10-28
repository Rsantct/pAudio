#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  subprocess as sp
from    time import sleep
import  json
from    camilladsp import CamillaConnection
import  make_eq as me


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


def set_level(dB):
    me.spl = me.LOUDNESS_REF_LEVEL + dB
    reload_eq()
    PC.set_volume(dB)
    return 'done'


def set_mute(mode):
    res = str( PC.set_mute(mode) )
    if res == 'None':
        res = 'done'
    return res


def get_state():
    """ This is the internal camillaDSP state """
    return json.dumps( str( PC.get_state() ) )


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
