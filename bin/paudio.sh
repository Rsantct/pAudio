#!/bin/bash

# Stopping audio
pkill -f "server.py paudio"
pkill -f "camilladsp.yml"

# Stopping control web page
pkill -f "paudio/code/share/www/nodejs"


if [[ $1 = *"stop"* ]]; then
    echo "stopped."
    exit 0


# Starting audio and control web page
elif [[ $1 = *"start"* ]]; then

    # Control web page
    node ~/paudio/code/share/www/nodejs_www_server/www-server.js >/dev/null 2>&1 &
    echo "pAudio web server running in background ..."

    # Verbose mode
    if [[ $2 = *"-v"* ]]; then

        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 -v
        pkill -f "paudio/code/share/www/nodejs"

    # Silent mode
    else

        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 1>/dev/null 2>&1 &
        echo "pAudio running in background ..."

    fi


else
    echo
    echo "  Usage:  paudio.sh [ start | stop ]  [ -v ]"
    echo "          -v:  verbose mode not detached from terminal"
    echo

fi

