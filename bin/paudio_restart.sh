#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

#
# This script just provides:
#   - a Python venv if available
#   - a DBUS_SESSION_BUS_ADDRESS if neccessary for JACK when not in a X environment
#

function start_www {

    if [[ $(pgrep -f "nodejs_www_server/www-server.js") ]]; then
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) pAudio web server is already running."
        fi

    else
        node $HOME/pAudio/code/share/www/nodejs_www_server/www-server.js 1>/dev/null 2>&1 &

    fi
}


function start_ctrl {

    if [[ $(pgrep -f "server.py paudio_ctrl") ]]; then
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) pAudio_ctrl server is already running."
        fi
    else
        python3 $HOME/pAudio/code/share/server.py paudio_ctrl 0.0.0.0 $CTRL_PORT 1>/dev/null 2>&1 &

    fi
}


function start_jack {

    # needed for headless machines
    if [[ ! $DBUS_SESSION_BUS_ADDRESS ]]; then
        export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
    fi

    # needs & for background running
    if [[ $VERBOSE == 'true' ]]; then
        python3 $HOME/pAudio/start.py --jack &

    else
        python3 $HOME/pAudio/start.py --jack 1>/dev/null 2>&1 &

    fi

    sleep 1
}


function start_camilladsp {

    if [[ $(uname) == "Linux" ]]; then
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) killing CamillaDSP."
        fi
        pkill -KILL -f camilladsp 1>/dev/null 2>&1
        sleep 1
    fi

    if [[ $(pgrep camilladsp) ]]; then
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) CamillaDSP is already running."
        fi

    else
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) Running CamillaDSP in wait mode ..."
        fi
        $HOME/bin/camilladsp --wait --mute \
            --address 127.0.0.1 --port $CAMILLADSP_PORT \
            --logfile $HOME/pAudio/log/camilladsp.log &
        sleep 2
    fi
}


function do_stop {

    python3 $HOME/pAudio/start.py stop                  # pAudio server

    if [[ $(uname) == "Linux" ]]; then
        pkill -KILL -f camilladsp 1>/dev/null 2>&1      # CamillaDSP
        sleep 1
        pkill -KILL -f 'jackd'    1>/dev/null 2>&1      # Jack
    fi
    sleep 1
}


function do_start {

    if [[ $(uname) == "Linux" ]]; then                  # Jack
        start_jack
    fi

    start_camilladsp                                    # CamillaDSP

    start_www                                           # Node WWW server

    start_ctrl                                          # pAudio control server

    if [[ $VERBOSE == 'true' ]]; then                   # pAudio server
        python3 $HOME/pAudio/start.py start $VERBOSE &
    else
        python3 $HOME/pAudio/start.py start 1> $HOME/pAudio/log/start.log \
                                            2> $HOME/pAudio/log/start.err &
    fi
}


# Python venv
if [[ ! $VIRTUAL_ENV ]]; then
    if [[ -f "$HOME/.env/bin/activate" ]]; then
        source $HOME/.env/bin/activate 1>/dev/null 2>&1
    fi
fi

# CamillaDSP port
CAMILLADSP_PORT=$(awk '/^camilladsp_port:/ {print $2}' FS=': ' $HOME/pAudio/config.yml)
if [[ ! $CAMILLADSP_PORT ]]; then
    CAMILLADSP_PORT=1234
fi

# pAudio port
PA_PORT=$(awk '/^paudio_port:/ {print $2}' FS=': ' $HOME/pAudio/config.yml)
if [[ ! $PA_PORT ]]; then
    PA_PORT=9990
fi
CTRL_PORT=$((PA_PORT + 1))

VERBOSE='false'

# Main
if [[ $1 == 'stop' ]]; then
    do_stop

elif [[ ! $1 || $1 == *'start' ]]; then

    if [[ $2 == *'-v'* ]]; then
        VERBOSE='true'
    fi
    echo $VERBOSE > $HOME/pAudio/.verbose

    do_stop

    do_start

else
    echo
    echo "USAGE:   paudio_restart.sh  [ stop |  start [-v] ]"
    echo "              -v   verbose mode"
    echo
fi
