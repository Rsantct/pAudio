#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

#
# This script just provides:
#   - a Python venv if available
#   - a DBUS_SESSION_BUS_ADDRESS if neccessary for JACK when not in a X environment
#


# Python venv
if [[ ! $VIRTUAL_ENV ]]; then
    if [[ -f "$HOME/.env/bin/activate" ]]; then
        source $HOME/.env/bin/activate 1>/dev/null 2>&1
    fi
fi


function do_stop {
    echo '(i) STOPPING pAudio'
    python3 $HOME/pAudio/start.py stop
}


function do_start {

    if [[ ! $DBUS_SESSION_BUS_ADDRESS ]]; then
        export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
    fi

    if [[ $1 == *"-v"* ]]; then
        echo "Starting pAudio in VERBOSE MODE"
        python3 $HOME/pAudio/start.py start -v &
    else
        echo "Starting pAudio in background."
        python3 $HOME/pAudio/start.py start 1>/dev/null 2>&1 &
    fi
}


if [[ $1 == 'stop' ]]; then
    do_stop

elif [[ ! $1 || $1 == *'start' ]]; then
    do_start $2

else
    echo
    echo "USAGE:   paudio_restart.sh  [ start |  stop ]"
    echo
fi
