#!/bin/bash

pkill -f "server.py paudio"
pkill -f "camilladsp.yml"
if [[ $1 = *"stop"* ]]; then
    echo "stopped."
    exit 0

# Verbose mode
elif [[ $1 = *"-v"* ]]; then
    python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 -v

# Silent mode
elif [[ $1 = *"start"* ]]; then
    python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 1>/dev/null 2>&1 &
    echo "server running in background ..."

else
    echo
    echo "  Usage:  paudio.sh [ start | stop | -v ]"
    echo "          -v:  verbose mode not detached from terminal"
    echo
fi

