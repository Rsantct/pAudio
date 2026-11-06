#!/usr/bin/env python3
""" dvbv5-scan (DVB-T1/T2) channels file converter to former Mplayer file format
"""
# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import os
import sys
import re

# Format for Mplayer DVB-T channels config:
# CHANNEL_NAME:FREQUENCY:INVERSION:BANDWIDTH:CODE_RATE_HP:CODE_RATE_LP:MODULATION:TRANSMISSION_MODE:GUARD_INTERVAL:HIERARCHY:VIDEO_PID:AUDIO_PID:SERVICE_ID
# Standard Mplayer values:
# FREQUENCY in Hz
# BANDWIDTH: 8MHz is usually represented as 8MHz or BANDWIDTH_8_MHZ or 8. In traditional mplayer channels.conf: 8MHz -> 8MHz or BANDWIDTH_8_MHZ.
# However, standard mplayer syntax for DVB-T:
# Name:frequency:inversion:bandwidth:coderateHP:coderateLP:modulation:transmissionMode:guardInterval:hierarchy:videoPID:audioPID:serviceID

def convert_dvbv5_to_mplayer(dvbv5_text):

    def make_line():
        # Mplayer format line:
        # Name:Frequency:Inversion:Bandwidth:CodeRateHP:CodeRateLP:Modulation:TransmissionMode:GuardInterval:Hierarchy:VideoPID:AudioPID:ServiceID
        line = f"{name2}:{freq}:{inv}:{bw_str}:{cr_hp}:{cr_lp}:{mod_str}:{tm_str}:{gi_str}:{hier_str}:{vpid}:{apid}:{sid}"
        return line


    mplayer_lines = []

    # Split blocks by bracketed names
    blocks = re.split(r'\n(?=\[)', dvbv5_text.strip())

    for block in blocks:
        if not block.strip():
            continue

        # Extract channel name
        name_match = re.search(r'\[(.*?)\]', block)
        if not name_match:
            continue
        name = name_match.group(1).strip()

        # Extract key-value pairs
        params = {}
        for line in block.split('\n'):
            if '=' in line:
                k, v = line.split('=', 1)
                params[k.strip()] = v.strip()

        freq = params.get('FREQUENCY', '0')
        inv = params.get('INVERSION', 'INVERSION_AUTO')
        if inv == 'AUTO': inv = 'INVERSION_AUTO'

        bw = params.get('BANDWIDTH_HZ', '8000000')
        if bw == '8000000':
            bw_str = 'BANDWIDTH_8_MHZ'
        else:
            bw_str = 'BANDWIDTH_AUTO'

        cr_hp = params.get('CODE_RATE_HP', 'AUTO')
        if cr_hp == 'AUTO': cr_hp = 'FEC_AUTO'

        cr_lp = params.get('CODE_RATE_LP', 'AUTO')
        if cr_lp == 'AUTO': cr_lp = 'FEC_AUTO'

        mod = params.get('MODULATION', 'QAM/64')
        if mod == 'QAM/64': mod_str = 'QAM_64'
        elif mod == 'AUTO': mod_str = 'QAM_AUTO'
        else: mod_str = mod.replace('/', '_')

        tm = params.get('TRANSMISSION_MODE', 'AUTO')
        if tm == 'AUTO': tm_str = 'TRANSMISSION_MODE_AUTO'
        else: tm_str = tm

        gi = params.get('GUARD_INTERVAL', 'AUTO')
        if gi == 'AUTO': gi_str = 'GUARD_INTERVAL_AUTO'
        else: gi_str = gi

        hier = params.get('HIERARCHY', 'NONE')
        if hier == 'NONE': hier_str = 'HIERARCHY_NONE'
        else: hier_str = hier

        vpid = params.get('VIDEO_PID', '0')

        sid = params.get('SERVICE_ID', '0')

        # AUDIO_PID can have multiple values,
        apid_raw = params.get('AUDIO_PID', '0').strip()
        apids = apid_raw.split()

        for apid in apids:
            if len(apids) > 1:
                name2 = f'{name} audio_pid_{apid}'
            else:
                name2 = name
            line = make_line()
            mplayer_lines.append(line)

    return mplayer_lines


def read_txt(fpath):
    try:
        with open(fpath, 'r') as f:
            res = f.read().strip()
            return res
    except:
        raise Exception(f'Error reading {fpath}')


if __name__ == "__main__":

    dvbv5_fpath = sys.argv[1]

    dvbv5_text = read_txt(dvbv5_fpath)

    mplayer_lines = convert_dvbv5_to_mplayer(dvbv5_text)

    d = os.path.dirname(dvbv5_fpath)
    b = os.path.basename(dvbv5_fpath)
    output_filename = f'{d}/{b}_mplayer'

    with open(output_filename, "w", encoding="utf-8") as f:
        tmp = "\n".join(mplayer_lines)
        f.write(tmp)

    print(f"Generated {output_filename} successfully.")
    print("\nFirst 20 lines of generated file:")
    print("\n".join(mplayer_lines[:20]))
