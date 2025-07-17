#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import os
import sys
UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from common import *

import jack_mod as jm

jm._jcli_activate('source_selector')


def get_sources():
    """
        - Scan for well known plugins then prepare
          their corresponding sources

        - Read other configured sources under jack: in config.yml
    """

    sources = [ {'name': 'none'} ]

    # Scan well known plugins
    for plugin in CONFIG.get('plugins'):

        # MPD
        if 'mpd' in plugin:

            sources.append( {
                'name':     'mpd',
                'jport':    'mpd_loop'
            } )

        # TODO
        # ....


    snames = [ x["name"] for x in sources ]


    # Other user defined sources
    if CONFIG["jack"].get('sources'):

        for source in CONFIG["jack"].get('sources'):

            if not source["name"] in snames:
                sources.append( source )

            else:
                print(f'{Fmt.BOLD}Jack source `{source["name"]}` is not needed when the plugin is used{Fmt.END}')


    return sources


def select(source):

    jm.clear_preamp()

    if source["name"] == 'none':
        return 'ordered'

    return jm.connect_bypattern(source["jport"], 'pre_in_loop')

