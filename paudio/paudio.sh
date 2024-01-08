#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.


BOLD=$(tput bold)
NORMAL=$(tput sgr0)

# Reading TCP address and port from the pe.audio.sy config file
ADDR=$( grep paudio_addr ~/paudio/config.yml | grep -v \# | awk '{print $NF}' )
ADDR=${ADDR//\"/}; CTL_ADDR=${ADDR//\'/}
PORT=$( grep paudio_port ~/paudio/config.yml | grep -v \# | awk '{print $NF}' )
if [[ ! $ADDR || ! $PORT ]]; then
    echo ${BOLD}
    echo '(i) Not found pAudio control TCP server address/port in `config.yml`,'
    echo '    using defaults `localhost:9980`'
    echo ${NORMAL}
    ADDR='localhost'
    PORT=9980
fi


function help {
    echo
    echo "  Usage:  paudio.sh   stop | start [ -v ] | toggle"
    echo "          -v:  verbose mode not detached from terminal"
    echo
}


function stop {
    # camilladsp
    pkill camilladsp
    # node web server
    pkill -f "paudio\/code\/"
    echo "pAudio has been stopped."
}


function restore {
    # Only for MacOS CoreAudio

    if [[ $(uname) == *'Darwin'* ]]; then
        echo "Restoring previous Default Playback Device"
        dev=$(cat ~/paudio/.previous_default_device)
        SwitchAudioSource -s "$dev"

        echo "Restoring previous Playback Device Volume"
        vol=$(cat ~/paudio/.previous_default_device_volume)
        osascript -e 'set volume output volume '$vol
    fi
}


function start {

    # Control web page
    node ~/paudio/code/share/www/nodejs_www_server/www-server.js >/dev/null 2>&1 &
    echo "pAudio web server running in background ..."

    # Audio in verbose mode
    if [[ $1 = *"-v"* ]]; then
        python3 ~/paudio/code/share/server.py paudio $ADDR $PORT -v
        pkill -f "paudio/code/share/www/nodejs"

    # Audio in silent mode
    else
        python3 ~/paudio/code/share/server.py paudio $ADDR $PORT 1>/dev/null 2>&1 &
        echo "pAudio running in background ..."

    fi
}


if [[ $1 = *"stop"* ]]; then

    stop
    restore

elif [[ $1 = *"start"* ]]; then

    stop
    start $2

elif [[ $1 = *"toggle"* ]]; then

    running=$(pgrep -f "paudio\/code\/")

    if [[ $running ]]; then
        stop
        restore
    else
        start
    fi

else
    help

fi

