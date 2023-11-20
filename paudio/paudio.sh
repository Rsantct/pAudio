#!/bin/bash

function help {
    echo
    echo "  Usage:  paudio.sh   stop | start [ -v ]"
    echo "          -v:  verbose mode not detached from terminal"
    echo
}


function stop {
    pkill -f "paudio\/code\/"
    echo "stopped."
}


if [[ $1 = *"stop"* ]]; then

    stop
    exit 0


elif [[ $1 = *"start"* ]]; then

    stop

    # Control web page
    node ~/paudio/code/share/www/nodejs_www_server/www-server.js >/dev/null 2>&1 &
    echo "pAudio web server running in background ..."

    # Audio in verbose mode
    if [[ $2 = *"-v"* ]]; then
        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 -v
        pkill -f "paudio/code/share/www/nodejs"

    # Audio in silent mode
    else
        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 1>/dev/null 2>&1 &
        echo "pAudio running in background ..."

    fi


else

    help


fi

