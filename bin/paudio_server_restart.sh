#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

PA_CFG_PATH=$HOME/pAudio/config/config.yml


BOLD="\033[1m"
RED="\033[0;31m"
BLUE="\033[0;34m"
GRAY="\033[0;90m"
NOCOLOR="\033[0m"


function do_stop {

    if [[ $(uname) == "Linux" ]]; then
        # be aware with the trailing space
        pkill -KILL -f "server.py paudio "

    else
        echo "Only works on Linux"
        exit -1

    fi
    sleep 1
}


function do_start {

    if [[ $VERBOSE == 'true' ]]; then                       # pAudio server
        python3 /home/paudio/pAudio/code/share/server.py paudio 0.0.0.0 $PA_PORT &
    else
        python3 /home/paudio/pAudio/code/share/server.py paudio 0.0.0.0 $PA_PORT \
            1> $HOME/pAudio/log/paudio_server.log \
            2> $HOME/pAudio/log/paudio_server.err &
    fi
}


# Python venv
if [[ ! $VIRTUAL_ENV ]]; then
    if [[ -f "$HOME/.env/bin/activate" ]]; then
        source $HOME/.env/bin/activate 1>/dev/null 2>&1
    fi
fi

# pAudio port
PA_PORT=$(awk '/^paudio_port:/ {print $2}' FS=': ' $PA_CFG_PATH)
if [[ ! $PA_PORT ]]; then
    PA_PORT=9990
fi


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
    echo "Restarts the pAudio commands processor server"
    echo
    echo "USAGE:   paudio_server_restart.sh  [ stop |  start [-v] ]"
    echo "              -v   verbose mode"
    echo
fi
