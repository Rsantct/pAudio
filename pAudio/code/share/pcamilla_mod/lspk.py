#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.


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
        'description':  f'DRC left ({pAudio_config["loudspeaker"]})',
        'channels':     [0],
        'bypassed':     False,
        'names':        []
    }
    pipeline_drc_R_step = {
        'type':         'Filter',
        'description':  f'DRC right ({pAudio_config["loudspeaker"]})',
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

        for param, filters in values.items():

            # skip any other parameters (i.e. gains)
            if not param in ('L', 'R'):
                continue

            else:
                ch = param

            for filter_id, filter_params in filters.items():

                tmp = f'drc_{set_name}_{filter_id:0>2}_{ch}'

                cam_config["filters"][tmp] = filter_params


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

        for param in pAudio_config["drc"][first_drc_set]:

            # skip any other parameters (i.e. gains)
            if not param in ('L', 'R'):
                continue
            else:
                ch = param

            for f in pAudio_config["drc"][first_drc_set][ch]:

                tmp = f'drc_{first_drc_set}_{f:0>2}_{ch}'

                if ch == 'L':
                    pipeline_drc_L_step_names.append(tmp)
                    print(f'{Fmt.BLUE}Adding filter `{tmp}` to pipeline `{pipeline_drc_L_step["description"]}`{Fmt.END}')

                if ch == 'R':
                    pipeline_drc_R_step_names.append(tmp)
                    print(f'{Fmt.BLUE}Adding filter `{tmp}` to pipeline `{pipeline_drc_R_step["description"]}`{Fmt.END}')


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
