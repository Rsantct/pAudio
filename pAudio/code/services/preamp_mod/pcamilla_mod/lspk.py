#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

from .do_makes import *

Fmt = None


def update_lspk(pAudio_config, cam_config):

    # 1. Prepare filters sections
    if not cam_config.get('filters'):
        cam_config["filters"] = {}


    # 2.a. Prepare pipeline steps for loudspeaker EQ
    pipeline_eq_L_step = {
        'type':         'Filter',
        'description':  f'{ pAudio_config["loudspeaker"] } (EQ left)',
        'channels':     [0],
        'bypassed':     False,
        'names':        []
    }
    pipeline_eq_R_step = {
        'type':         'Filter',
        'description':  f'{ pAudio_config["loudspeaker"] } (EQ right)',
        'channels':     [1],
        'bypassed':     False,
        'names':        []
    }
    pipeline_eq_L_step_names = []
    pipeline_eq_R_step_names = []


    # 2.b. Prepare pipeline steps for DRC
    pipeline_drc_L_step = {
        'type':         'Filter',
        'description':  f'{ pAudio_config["loudspeaker"] } (DRC left)',
        'channels':     [0],
        'bypassed':     False,
        'names':        []
    }
    pipeline_drc_R_step = {
        'type':         'Filter',
        'description':  f'{ pAudio_config["loudspeaker"]} (DRC right)',
        'channels':     [1],
        'bypassed':     False,
        'names':        []
    }
    pipeline_drc_L_step_names = []
    pipeline_drc_R_step_names = []


    # 3. Import the filters pAudio_config ---> cam_config

    # 3.a. Loudspeaker EQ filters
    for fname, fparams in pAudio_config.get('lspk_eq', {}).items():
        cam_config["filters"][fname] = fparams

    # 3.b. DRC filters
    for set_name, values in pAudio_config.get('drc', {}).items():

        # FIR have only the drc-set-name as values, so we need
        # to REPLACE it with the whole parameters for both channels.
        if values == 'fir':

            fs = pAudio_config["samplerate"]
            lspkfolder = f'{pAudio_config["mainfolder"]}/loudspeakers/{pAudio_config["loudspeaker"]}'

            values = {'L': {}, 'R': {}}
            values["L"]["1"] = make_drc_fir_filter('L', set_name, fs, lspkfolder)
            values["R"]["1"] = make_drc_fir_filter('R', set_name, fs, lspkfolder)
            pAudio_config["drc"][set_name] = values

        # Now FIR or IIR must have a regular complete filter syntax
        if 'L' in values or 'R' in values:

            for ch, filters in values.items():

                for filter_id, filter_params in filters.items():

                    filter_id = f'drc_{set_name}_{filter_id}_{ch}'

                    cam_config["filters"][filter_id] = filter_params


    # 4. Append to pipeline

    # 4.a. Loudspeaker EQ filters
    for f in pAudio_config.get('lspk_eq', {}):

        # Common filters for both channels
        if f[:-2] not in ('_L', '_R'):

            pipeline_eq_L_step_names.append(f)
            print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_L_step["description"]}`{Fmt.END}')
            pipeline_eq_R_step_names.append(f)
            print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_R_step["description"]}`{Fmt.END}')

        # Filters for an specific channel
        else:

            if f[:-2] == '_L':
                pipeline_eq_L_step_names.append(f)
                print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_L_step["description"]}`{Fmt.END}')

            if f[:-2] == '_R':
                pipeline_eq_R_step_names.append(f)
                print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_R_step["description"]}`{Fmt.END}')


    # 4.b. DRC filters (will use the first drc set found as initial configuration)
    drc_sets = pAudio_config.get('drc', {})

    if drc_sets:

        first_drc_set = next( iter( drc_sets.keys() ) )

        for ch in pAudio_config["drc"][first_drc_set]:

            for f in pAudio_config["drc"][first_drc_set][ch]:

                f = f'drc_{first_drc_set}_{f}_{ch}'

                if ch == 'L':
                    pipeline_drc_L_step_names.append(f)
                    print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_drc_L_step["description"]}`{Fmt.END}')

                if ch == 'R':
                    pipeline_drc_R_step_names.append(f)
                    print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_drc_R_step["description"]}`{Fmt.END}')


    # 5. Populate step names
    pipeline_eq_L_step["names"] = pipeline_eq_L_step_names
    pipeline_eq_R_step["names"] = pipeline_eq_R_step_names

    pipeline_drc_L_step["names"] = pipeline_drc_L_step_names
    pipeline_drc_R_step["names"] = pipeline_drc_R_step_names

    # 6. Then append pipeline steps if used
    if pipeline_eq_L_step["names"] or pipeline_eq_R_step["names"] :
        cam_config["pipeline"].append( pipeline_eq_L_step )
        cam_config["pipeline"].append( pipeline_eq_R_step )

    if pipeline_drc_L_step["names"] or pipeline_drc_R_step["names"] :
        cam_config["pipeline"].append( pipeline_drc_L_step )
        cam_config["pipeline"].append( pipeline_drc_R_step )
