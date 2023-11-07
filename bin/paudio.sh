#!/bin/bash

pkill -f "server.py paudio"
pkill -f "camilladsp.yml"

if [[ $1 = *"stop"* ]]; then
    echo "stopped."
    exit 0


elif [[ $1 = *"start"* ]]; then

    # Verbose mode
    if [[ $2 = *"-v"* ]]; then
        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 -v

    # Silent mode
    else
        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 1>/dev/null 2>&1 &
        echo "server running in background ..."
    fi

else
    echo
    echo "  Usage:  paudio.sh [ start | stop ]  [ -v ]"
    echo "          -v:  verbose mode not detached from terminal"
    echo
fi

