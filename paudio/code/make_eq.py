#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  numpy as np
import  os
import  sys
UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/audiotools')
from    tools import semispectrum2impulse, savePCM32


# Module constants
LOUDNESS_REF_LEVEL = 83
FS                 = 44100
EQ_PCM_PATH        = '../eq/eq.pcm'
#
CURVES_FOLDER = f'{UHOME}/audiotools/convolver_eq/curves_{FS}_N11'
BASS_PATH     = f'{CURVES_FOLDER}/bass_mag.dat'
TREB_PATH     = f'{CURVES_FOLDER}/treble_mag.dat'
LOUD_PATH     = f'{CURVES_FOLDER}/ref_{LOUDNESS_REF_LEVEL}_loudness_mag.dat'
LOUD_CURVES   = np.loadtxt(LOUD_PATH)
BASS_CURVES   = np.loadtxt(BASS_PATH)
TREB_CURVES   = np.loadtxt(TREB_PATH)

# Module global variables (initial values)
bass            = 0
treble          = 0
spl             = 83.0
target          = '+0.0-0.0'
equal_loudness  = False


def save_eq_IR(pcm_path=EQ_PCM_PATH, mag_is_dB=True):
    # curve to FIR
    imp = semispectrum2impulse(eq, dB=mag_is_dB)
    savePCM32(imp, pcm_path)


def make_tone_curve():
    """ Combina bass y treble
        Hay 25 curvas desde -12 hasta +12 dB, la cero es [12,:]
        Valores redondeados en saltos de 1 dB
    """
    b = int(round(bass))
    t = int(round(treble))
    if abs(b) > 12 or abs(t) > 12:
        raise Exception('Tone values must be in +/- 12 dB')
    bass_idx = b + 12
    treb_idx = t + 12
    bass_curve = BASS_CURVES[bass_idx, :]
    treb_curve = TREB_CURVES[treb_idx, :]
    return bass_curve + treb_curve


def get_target(targetID):
    target_path = f'{CURVES_FOLDER}/room_target/{targetID}_target_mag.dat'
    return np.loadtxt(target_path)


def get_loudness(curve_index):
    max_index = LOUD_CURVES.shape[0] - 1
    curve_index = min(max_index, max(0, curve_index))
    return LOUD_CURVES[curve_index, :]


def make_eq():
    """ Composing EQ
    """

    global eq

    if equal_loudness:
        loudness_curve_index = int(round(spl))

    else:
        loudness_curve_index = LOUDNESS_REF_LEVEL

    eq =   make_tone_curve() \
         + get_loudness(loudness_curve_index) \
         + get_target(target)


if __name__ == "__main__":

    # only for testing from command line
    for opc in sys.argv[1:]:
        if '-b' in opc:
            bass = int( opc.split("=")[-1])
        if '-t' in opc:
            treble = int( opc.split("=")[-1])
    eqcurve = make_eq()
    save_eq_IR(eqcurve)
