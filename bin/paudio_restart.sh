#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

#
# This script just provides:
#   - a Python venv if available
#   - a DBUS_SESSION_BUS_ADDRESS if neccessary for JACK when not in a X environment
#

function start_camilladsp {

    if [[ $(pgrep camilladsp) ]]; then
        echo "CamillaDSP is already running."

    else
        echo "Running CamillaDSP in wait mode ..."
        $HOME/bin/camilladsp --wait --mute \
            --address 127.0.0.1 --port 1234 \
            --logfile $HOME/pAudio/log/camilladsp.log &
    fi
}


function start_pAudio_www {

    if [[ $(pgrep -f "nodejs_www_server/www-server.js") ]]; then
        echo "pAudio web server is already running."

    else
        node $HOME/pAudio/code/share/www/nodejs_www_server/www-server.js 1>/dev/null 2>&1 &

    fi
}


function start_pAudio_ctrl {

    if [[ $(pgrep -f "server.py paudio_ctrl") ]]; then
        echo "pAudio_ctrl server is already running."

    else
        python3 $HOME/pAudio/code/share/server.py paudio_ctrl 0.0.0.0 $CTRL_PORT &

    fi
}


function start_pAudio_server {

    if [[ $(pgrep -f "server.py paudio ") ]]; then
        echo "pAudio server is already running."

    else
        python3 $HOME/pAudio/code/share/server.py paudio 0.0.0.0 $PA_PORT &

    fi
}


function start_pAudio_stuff {

    VERBOSE=''
    if [[ $1 == *"-v"* || $2 == *"-v"* ]]; then
        VERBOSE='-v'
    fi

    if [[ $VERBOSE == '-v' ]]; then
        echo "Starting pAudio in VERBOSE MODE"
        python3 $HOME/pAudio/start.py start $VERBOSE &

    else
        echo "Starting pAudio in background."
        python3 $HOME/pAudio/start.py start 1> $HOME/pAudio/log/start.log \
                                            2> $HOME/pAudio/log/start.err &
    fi
}


function do_stop {

    # Notice: CamillaDSP, the web server and the paudio_ctrl server
    #         remains intact from here

    echo '(i) STOPPING pAudio stuff'
    python3 $HOME/pAudio/start.py stop

    echo '(i) STOPPING pAudio server'
    pkill -f "server.py paudio "

    sleep 1
}


function do_start {

    if [[ ! $DBUS_SESSION_BUS_ADDRESS ]]; then
        export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
    fi

    start_camilladsp

    start_pAudio_www

    start_pAudio_ctrl

    start_pAudio_server

    start_pAudio_stuff $1 $2
}


# Python venv
if [[ ! $VIRTUAL_ENV ]]; then
    if [[ -f "$HOME/.env/bin/activate" ]]; then
        source $HOME/.env/bin/activate 1>/dev/null 2>&1
    fi
fi


# pAudio port
PA_PORT=$(awk '/^paudio_portx:/ {print $2}' FS=': ' $HOME/pAudio/config.yml)
if [[ ! $PA_PORT ]]; then
    PA_PORT=9990
fi
CTRL_PORT=$((PA_PORT + 1))


# Main
if [[ $1 == 'stop' ]]; then
    do_stop

elif [[ ! $1 || $1 == *'start' ]]; then
    do_stop
    do_start $2 $3

else
    echo
    echo "USAGE:   paudio_restart.sh  [ stop |  start [-v] ]"
    echo "              -v   verbose mode"
    echo
fi
