#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

"""
    A very simple YAML parser, useful for shell scripts

    Usage:    yparser.py   path/to/file.yml  [key]
"""

import yaml
import json
import sys


def read_file(fpath):
    with open(fpath, 'r') as f:
        tmp = f.read()
        d = yaml.safe_load(tmp)
    return d


if __name__ == "__main__":

    fpath = ''
    key = ''

    if sys.argv[1:]:

        fpath = sys.argv[1]

        if sys.argv[2:]:
            key = sys.argv[2]

    if key:

        d = read_file(fpath)
        val = d[key]

        if type(val) in (int, str):
            print(val)
        else:
            print(json.dumps(val))

    elif fpath:
        d = read_file(fpath)
        print(json.dumps(d))

    else:
        print(__doc__)
