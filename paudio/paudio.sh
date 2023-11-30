#!/bin/bash

function help {
    echo
    echo "  Usage:  paudio.sh   stop | start [ -v ]"
    echo "          -v:  verbose mode not detached from terminal"
    echo
}


function stop {
    pkill -f "paudio\/code\/"
    echo "pAudio has been stopped."
}


function restore {
    echo "Restoring previous Default Playback Device"
    dev=$(cat ~/paudio/.previous_default_device)
    SwitchAudioSource -s "$dev"

    echo "Restoring previous Playback Device Volume"
    vol=$(cat ~/paudio/.previous_default_device_volume)
    osascript -e 'set volume output volume '$vol
}


function start {

    # Control web page
    node ~/paudio/code/share/www/nodejs_www_server/www-server.js >/dev/null 2>&1 &
    echo "pAudio web server running in background ..."

    # Audio in verbose mode
    if [[ $1 = *"-v"* ]]; then
        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 -v
        pkill -f "paudio/code/share/www/nodejs"

    # Audio in silent mode
    else
        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 1>/dev/null 2>&1 &
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

