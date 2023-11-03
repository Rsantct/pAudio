#!/bin/bash

pkill -f "server.py paudio"
pkill -f "camilladsp.yml"
if [[ $1 = *"-s"* ]]; then
    echo "stopped."
    exit 0
fi

# Verbose mode
if [[ $1 = *"-v"* ]]; then
    python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 -v

# Silent mode
else
    python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 1>/dev/null 2>&1 &
    echo "server running in background ..."
fi
