#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

import os
import sys
UHOME       = os.path.expanduser('~')
MAINFOLDER  = f'{UHOME}/pAudio'
sys.path.append(f'{MAINFOLDER}/code/share')

from   common   import *

import jack_mod as jm

SOURCES = {}


def _init():
    get_sources()


def get_sources():
    """
        - Scan for well known plugins then prepare
          their corresponding source

        - Read other configured sources under jack: in config.yml
    """

    def get_remote_source_addr_port(remote_addr):
        """ Gets the IP:CTRLPORT as configured under 'remote_addr'
            in a remoteXXXXX kind of configured source.
        """
        addr = ''
        port = 9990

        try:
            tmp_addr = remote_addr.split(':')[0]
            tmp_port = remote_addr.split(':')[-1]

            if is_IP(tmp_addr):
                addr = tmp_addr
            else:
                print(f'(common) source: \'{sname}\' address: \'{tmp_addr}\' is NOT valid')

            if tmp_port.isdigit():
                port = int(tmp_port)

        except Exception as e:
            print(f'(sources) ERROR reading remote_addr: {str(e)}')

        return addr, port


    global SOURCES

    if not CONFIG.get("jack"):
        return { 'system-wide': {} }

    sources = { 'none': {} }

    # Scan for well known plugins and prepare the appropriate source
    for plugin in CONFIG.get('plugins'):

        # Create an 'mpd' pAudio soure
        if 'mpd' in plugin:
            sources["mpd"] = { 'jport': 'mpd_loop'}

        # TODO
        # ....


    # Other user defined sources
    if CONFIG["jack"].get('sources'):

        for jsource, params in CONFIG["jack"].get('sources').items():

            if not jsource in sources:

                sources[jsource] = params

                # Complete other parameters for remote sources
                if 'remote' in jsource:

                    ip, port = get_remote_source_addr_port(params["remote_addr"])
                    jport = f'zita_n2j_{ip.split(".")[-1]}'
                    sources[jsource]["ip"]    = ip
                    sources[jsource]["port"]  = port
                    sources[jsource]["jport"] = jport

                    del sources[jsource]["remote_addr"]

            # It is a predefined source because we created it before
            # for well-known sources, for example for the mpd.py plugin
            else:
                for k, v in params.items():
                    sources[jsource][k] = v

    SOURCES = sources

    return sources


def select(source):

    # open a temporary jack.Client
    tmp = jm._jcli_activate('source_selector')

    if tmp == 'done':
        jm.clear_preamp()

        if source == 'none':
            return 'ordered'

        res = jm.connect_bypattern( SOURCES[source]["jport"], 'pre_in_loop' )

        # close the temporary jack.Client
        del jm.JCLI

        return res

    else:
        return tmp

_init()
