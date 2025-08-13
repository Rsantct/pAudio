#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" This program makes PNG graphs for the drc sets found inside

        <LSPKFOLDER>/lspk.yml

    PNG files are saved for the control web page to be displayed
"""

import  sys
import  matplotlib.pyplot   as plt
import  numpy               as np
from    scipy               import signal

from    common              import *
import  audiotools.audio_eq_cook_book as eqbook

FACECOLOR = (.15, .15, .15)     # like pAudio web page

IMGFOLDER = f'{MAINFOLDER}/code/share/www/images/{LOUDSPEAKER}'

VERBOSE   = False


def get_filter_ab_coeffs(fcamilla_name, fcamilla_params):
    """ Currently only Biquad filters of type
        - 'Peaking'
        - 'LinkwitzTransform'
    """

    filter_type = fcamilla_params.get('type')
    parameters  = fcamilla_params.get('parameters')

    if filter_type == 'Biquad' and isinstance(parameters, dict):

        param_type = parameters.get('type')

        if param_type == 'Peaking':

            freq = parameters.get('freq')
            gain = parameters.get('gain')
            q = parameters.get('q')

            if all(v is not None for v in [freq, gain, q]):

                try:
                    ab_coeffs = eqbook.peaking_biquad_coefficients(freq, gain, q, fs)

                    if VERBOSE:
                        print(fcamilla_name, parameters)

                except Exception as e:
                    print(f"{Fmt.RED}'{fcamilla_name}' (Peaking): error when calculating coefficients: {e}{Fmt.END}")

            else:
                print(f"{Fmt.RED}'{fcamilla_name}' (Peaking): bad paramenters{Fmt.END}")

        elif param_type == 'LinkwitzTransform':

            freq_act    = parameters.get('freq_act')
            q_act       = parameters.get('q_act')
            freq_target = parameters.get('freq_target')
            q_target    = parameters.get('q_target')

            if all(v is not None for v in [freq_act, q_act, freq_target, q_target]):

                try:
                    ab_coeffs = eqbook.linkwitz_transform_coefficients(freq_act, q_act, freq_target, q_target, fs)

                    if VERBOSE:
                        print(filter_coeffs[fcamilla_name])

                except Exception as e:
                    print(f"{Fmt.RED}'{fcamilla_name}' (LinkwitzTransform): error when calculating coefficients: {e}{Fmt.END}")

            else:
                print(f"{Fmt.RED}'{fcamilla_name}' (LinkwitzTransform): bad paramenters{Fmt.END}")

        else:
            print(f"{Fmt.RED}'{fcamilla_name}' ({param_type}): NOT supported{Fmt.END}")


    return ab_coeffs


def prepare_plot():

    # custom Coordinate Formatter for status bar
    def custom_format_coord(x, y):
        """
        Formats the x and y coordinates for the status bar.
        """
        # You can customize the precision here (e.g., :.1f for one decimal place)
        return f'x={x:.0f}, y={y:.1f}'


    plt.style.use('dark_background')
    plt.rcParams.update({'font.size': 6})
    plt.rcParams['lines.linewidth'] = 3

    FREQ_LIMITS = [20, 20000]
    FREQ_TICKS  = [20, 50, 100, 200, 500, 1e3, 2e3, 5e3, 1e4, 2e4]
    FREQ_LABELS = ['20', '50', '100', '200', '500', '1K', '2K', '5K', '10K', '20K']
    DB_LIMITS   = [-20, +9]
    DB_TICKS    = [-18, -12, -6, 0, 6]
    DB_LABELS   = ['-18', '-12', '-6', '0', '6']


    fig, ax_mag = plt.subplots()
    fig.set_figwidth( 5 )   # 5 inches at 100dpi => 500px wide
    fig.set_figheight( 1.5 )
    fig.set_facecolor( FACECOLOR )
    ax_mag.set_facecolor( FACECOLOR )

    ax_mag.set_title( 'DRC-IIR' )

    #ax_mag.set_xlabel('Hz')
    #ax_mag.set_ylabel('dB')
    ax_mag.grid(False)
    ax_mag.semilogx()
    ax_mag.set_ylim(DB_LIMITS)
    ax_mag.set_xlim(FREQ_LIMITS)
    ax_mag.set_xticks(FREQ_TICKS, FREQ_LABELS)
    ax_mag.set_yticks(DB_TICKS, DB_LABELS)

    # no subplot for phase
    ax_pha = None

    ax_mag.format_coord = custom_format_coord

    return ax_mag, ax_pha


def plot_frequency_response(set_name, filters_L_R):
    """
        set_name:   string

        filters_L_R:    { 'L':  { 1: { 'type': 'Biquad',
                                       'parameters': {'type': 'Peaking',
                                                      'freq': 53.8,
                                                      'gain': -2.0,
                                                      'q': 4.645
                                                      }
                                      }
                                  2: ....
                                },

                          'R':  { ...
                                }
                        }
    """

    if VERBOSE:
        print('\n--------')

    # If not L or not R
    for ch in ('L', 'R'):
        if not ch in filters_L_R:
            filters_L_R[ch] = {}

    # Subplots for magnitude, phase, group_delay
    ax_mag, ax_pha = prepare_plot()

    # Colors for each channel
    colors = ['steelblue', 'indianred']

    # Generate an array of base frequencies for all calculations
    # This ensures that all responses are calculated at the same frequency points.
    w_freqs, _ = signal.freqz([1], [1], worN=8192, fs=fs)

    traces_count = 0
    for ch, filters in filters_L_R.items():

        # Initialize with ones for multiplication
        h_combined_channel = np.ones_like(w_freqs, dtype=complex)


        if VERBOSE:
            print(f"{set_name} {ch}, processing biquads: {list(filters.keys())}")


        for fcamilla_name, fcamilla_params in filters.items():

            b, a                = get_filter_ab_coeffs(fcamilla_name, fcamilla_params)

            _, h_individual     = signal.freqz(b, a, worN=8192, fs=fs)

            h_combined_channel  *= h_individual

        combined_magnitude_db  = 20 * np.log10(abs(h_combined_channel))

        line_color = colors[traces_count]

        ax_mag.plot(w_freqs, combined_magnitude_db, label=ch, color=line_color)

        traces_count += 1


    if traces_count > 0:

        ax_mag.legend( facecolor=FACECOLOR, loc='lower right')
        png_path = f'{IMGFOLDER}/drc_{set_name}.png'
        plt.savefig( png_path, facecolor=FACECOLOR )
        print(f'(drc_iif2png) saved: {png_path})')

        if VERBOSE:
            plt.show()

    else:
        print("Nothing to plot")
        plt.close()


if __name__ == "__main__":

    for opc in sys.argv[1:]:

        if '-v' in opc:
            VERBOSE = True

        elif '-h' in opc:
            print(__doc__)
            sys.exit()


    sp.Popen(f'mkdir -p {IMGFOLDER}', shell=True)

    drc_sets = CONFIG["drc"]

    fs       = CONFIG["samplerate"]

    for set_name, filters_L_R in drc_sets.items():

        # IIR drc sets have 'L' and/or 'R' fields
        # FIR drc sets does not (see GitHub doc)
        if 'L' in filters_L_R or 'R' in filters_L_R:
            plot_frequency_response(set_name, filters_L_R)

