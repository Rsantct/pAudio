#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    Dumps the EQ FIR in use to a .png file
"""

import  numpy as np
from    scipy       import signal, fft
from    matplotlib  import pyplot as plt, use as matplotlib_use
import  sys
import  os

# https://matplotlib.org/faq/howto_faq.html#working-with-threads
# We need to call matplotlib.use('Agg') to replace the regular display backend
# (e.g. 'Mac OSX') by the dummy one 'Agg' in order to avoid incompatibility
# when threading the matplotlib when importing this stuff.
# Notice below that we dont order plt.show() but plt.close('all').
matplotlib_use('Agg')

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pAudio/code/share')

from common import *

EQFIR_PATH  = f'{EQFOLDER}/eq.pcm'
IMGFOLDER   = f'{MAINFOLDER}/code/share/www/images'
EQPNG_PATH  = f'{IMGFOLDER}/eq.png'

# ----------------------    Plot config      -----------------------------------
# Same color as index.html background-color: rgb(38, 38, 38)
WEBCOLOR    = (.15, .15, .15)
# https://matplotlib.org/2.0.2/examples/color/named_colors.html
plt.style.use('dark_background')
plt.rcParams.update({'font.size': 6})
FREQ_LIMITS = [20, 20000]
FREQ_TICKS  = [20, 50, 100, 200, 500, 1e3, 2e3, 5e3, 1e4, 2e4]
FREQ_LABELS = ['20', '50', '100', '200', '500', '1K', '2K', '5K', '10K', '20K']
DB_LIMITS   = [-9, +21]
DB_TICKS    = [-6, 0, 6, 12, 18]
DB_LABELS   = ['-6', '0', '6', '12', '18']


def readPCM(fname):
    """ reads impulse from a pcm float32 file
    """
    #return np.fromfile(fname, dtype='float32')
    return np.memmap(fname, dtype='float32', mode='r')


def get_spectrum(imp, fs):

    fNyq = fs / 2.0

    # Oversampling short taps IRs to display "hi-res" low freq region.
    N = int( len(imp) / 2 ) * 8
    # limit to N <= fs / 5 (a resolution of 5 Hz is enough for this graph)
    N = int(min(N, fs / 5))
    try:
        N = fft.next_fast_len(N)
    except:
        print(f'(eqfir2png) fft.next_fast_len not availble on this scipy version')

    # Semispectrum (whole=False -->  w to Nyquist)
    w, h = signal.freqz(imp, worN=N, whole=False)

    # Actual freq from normalized freq
    freqs = w / np.pi * fNyq

    # Magnitude to dB:
    magdB = 20 * np.log10(abs(h))

    return freqs, magdB


def init():
    # Prepare images folder
    try:
        os.mkdir(IMGFOLDER)
    except FileExistsError:
        pass
    except:
        print(f'(eqfir2png) unexpected error whith mkdir "{IMGFOLDER}"')


def fir2png(firpath=EQFIR_PATH):
    """ Do plot a png from a pcm FIR file
    """
    fig, ax = plt.subplots()
    fig.set_figwidth( 5 )   # 5 inches at 100dpi => 500px wide
    fig.set_figheight( 1.5 )
    fig.set_facecolor( WEBCOLOR )
    ax.set_facecolor( WEBCOLOR )

    ax.set_xscale('log')
    ax.set_xlim( FREQ_LIMITS )
    ax.set_xticks( FREQ_TICKS )
    ax.set_xticklabels( FREQ_LABELS )

    ax.set_ylim( DB_LIMITS )
    ax.set_yticks( DB_TICKS )
    ax.set_yticklabels( DB_LABELS )

    ax.set_title( 'EQ' )

    freqs, magdB = get_spectrum( readPCM(firpath), CONFIG["fs"] )

    ax.plot(freqs, magdB, color='grey', linewidth=3)

    plt.savefig( EQPNG_PATH, facecolor=WEBCOLOR )
    #plt.show()
    plt.close('all')


init()


# for command line usage
if __name__ == '__main__':

    fir2png(EQFIR_PATH)
    print( f'(eqfir2png) saved: \'{EQPNG_PATH}\' ' )

