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


function stop_pAudio_server {
    echo '(i) STOPPING pAudio'
    python3 $HOME/pAudio/start.py stop
}


function run_camilladsp {

    echo "Running CamillaDSP in wait mode ..."

    $HOME/bin/camilladsp --wait --mute \
        --address 127.0.0.1 --port 1234 \
        --logfile $HOME/pAudio/log/camilladsp.log &
}


function restart_pAudio_server {

    VERBOSE=''
    if [[ $1 == *"-v"* || $2 == *"-v"* ]]; then
        VERBOSE='-v'
    fi

    ONLY_SERVER=''
    if [[ $1 == *"-s"* || $2 == *"-s"* ]]; then
        ONLY_SERVER='-s'
    fi

    if [[ $VERBOSE == '-v' ]]; then
        echo "Starting pAudio in VERBOSE MODE"
        python3 $HOME/pAudio/start.py start $VERBOSE $ONLY_SERVER &

    else
        echo "Starting pAudio in background."
        python3 $HOME/pAudio/start.py start 1> $HOME/pAudio/log/start.log \
                                            2> $HOME/pAudio/log/start.err &
    fi
}


function do_start {

    if [[ ! $DBUS_SESSION_BUS_ADDRESS ]]; then
        export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
    fi

    if [[ $(pgrep camilladsp) ]]; then
        echo "CamillaDSP is already running."
    else
        run_camilladsp
    fi

    restart_pAudio_server $1 $2
}


if [[ $1 == 'stop' ]]; then
    stop_pAudio_server

elif [[ ! $1 || $1 == *'start' ]]; then
    do_start $2 $3

else
    echo
    echo "USAGE:   paudio_restart.sh  [ stop |  start [-v] [-s] ]"
    echo "              -v   verbose mode"
    echo "              -s   only server (skip audio backend)"
    echo
fi
