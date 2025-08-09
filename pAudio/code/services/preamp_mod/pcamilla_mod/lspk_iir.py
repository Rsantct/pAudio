#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

Fmt = None


def update_lspk_iir(pAudio_config, cam_config):

    # Prepare filters sections
    if not cam_config.get('filters'):
        cam_config["filters"] = {}


    # Prepare pipeline steps for loudspeaker EQ
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


    # Prepare pipeline steps for DRC
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


    # Import the filters pAudio_config ---> cam_config

    #   Loudspeaker EQ filters
    for fname, fparams in pAudio_config["iir_eq"].get('lspk_eq', {}).items():
        cam_config["filters"][fname] = fparams

    #   DRC filters
    for drc_set, drc_filters in pAudio_config["iir_eq"].get('drc', {}).items():
        for ch in pAudio_config["iir_eq"]["drc"][drc_set]:
            for fname, fparams in pAudio_config["iir_eq"]["drc"][drc_set][ch].items():
                fname = f'drc_{drc_set}_{fname}_{ch}'
                cam_config["filters"][fname] = fparams


    # Append loudspeaker EQ filters to pipeline
    for f in pAudio_config["iir_eq"].get('lspk_eq', {}):

        # Common filters for both channels
        if f[:-2] not in ('_L', '_R'):

            pipeline_eq_L_step_names.append(f)
            print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_L_step["description"]}`{Fmt.END}')
            pipeline_eq_R_step_names.append(f)
            print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_R_step["description"]}`{Fmt.END}')

        # Filters for an specific chennel
        else:

            if f[:-2] == '_L':
                pipeline_eq_L_step_names.append(f)
                print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_L_step["description"]}`{Fmt.END}')

            if f[:-2] == '_R':
                pipeline_eq_R_step_names.append(f)
                print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_eq_R_step["description"]}`{Fmt.END}')


    # Append loudspeaker DRC filters to pipeline
    # (first set found at init)
    drc_sets = pAudio_config["iir_eq"].get('drc', {})

    if drc_sets:

        first_drc_set = next( iter(drc_sets) )

        for ch in pAudio_config["iir_eq"]["drc"][first_drc_set]:

            for f in pAudio_config["iir_eq"]["drc"][first_drc_set][ch]:

                f = f'drc_{first_drc_set}_{f}_{ch}'

                if ch == 'L':
                    pipeline_drc_L_step_names.append(f)
                    print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_drc_L_step["description"]}`{Fmt.END}')

                if ch == 'R':
                    pipeline_drc_R_step_names.append(f)
                    print(f'{Fmt.BLUE}Adding filter `{f}` to pipeline `{pipeline_drc_R_step["description"]}`{Fmt.END}')


    # Populate step names
    pipeline_eq_L_step["names"] = pipeline_eq_L_step_names
    pipeline_eq_R_step["names"] = pipeline_eq_R_step_names

    pipeline_drc_L_step["names"] = pipeline_drc_L_step_names
    pipeline_drc_R_step["names"] = pipeline_drc_R_step_names

    # Then append pipeline steps if used
    if pipeline_eq_L_step["names"] or pipeline_eq_R_step["names"] :
        cam_config["pipeline"].append( pipeline_eq_L_step )
        cam_config["pipeline"].append( pipeline_eq_R_step )

    if pipeline_drc_L_step["names"] or pipeline_drc_R_step["names"] :
        cam_config["pipeline"].append( pipeline_drc_L_step )
        cam_config["pipeline"].append( pipeline_drc_R_step )
