#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.


def clear_filters(cfg, pattern=''):
    if pattern:
        keys = []
        for f in cfg["filters"]:
            if f.startswith(pattern):
                keys.append(f)
        for k in keys:
            del cfg["filters"][k]


def clear_mixers(cfg, pattern=''):
    if pattern:
        keys = []
        for m in cfg["mixers"]:
            if m.startswith(pattern):
                keys.append(m)
        for k in keys:
            del cfg["mixers"][k]


def clear_pipeline_input_filters(cfg, pattern=''):
    """ Clears elements inside the 2 first filters of the pipeline.
        That is, the pipeline steps 1 and 2
    """
    if pattern:
        for n in (1, 2):
            names_old = cfg["pipeline"][n]['names']
            names_new = list_remove_by_pattern(names_old, pattern)
            cfg["pipeline"][n]['names'] = names_new


def clear_pipeline_output_filtering(cfg):
    """ Remove output xo Filter steps from pipeline
    """
    p_old = cfg["pipeline"]
    p_new = []

    for step in p_old:
        if step["type"] != 'Filter':
            p_new.append(step)
        else:
            names = step["names"]
            if not [n for n in names if 'xo' in n]:
                p_new.append(step)

    cfg["pipeline"] = p_new


def clear_pipeline_mixer(cfg, pattern=''):
    """ Clears mixer steps from the pipeline
    """
    def remove_mixer(l, p):
        l = [ x for x in l
                if (x["type"]=='Mixer' and p not in x["name"])
                   or
                   x["type"]!='Mixer'
            ]
        return l

    if pattern:
        steps_old = cfg["pipeline"]
        steps_new = remove_mixer(steps_old, pattern)
        cfg["pipeline"] = steps_new


