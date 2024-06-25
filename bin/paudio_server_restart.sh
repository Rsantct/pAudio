#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

echo !!!
echo PENDING TO SPLIT CORE AND SERVER
echo !!!
exit 0


# Python venv
if [[ ! $VIRTUAL_ENV ]]; then
    if [[ -f "$HOME/.env/bin/activate" ]]; then
        source /home/paudio/.env/bin/activate 1>/dev/null 2>&1
    fi
fi


BOLD=$(tput bold)
NORMAL=$(tput sgr0)

SERVERPATH="$HOME"/"pAudio/code/share/server.py"

opc=$1

# Reading TCP address and port from the pe.audio.sy config file
YPARSER="$HOME"/"pAudio/code/share/yparser.py"
CFGPATH="$HOME"/"pAudio/config.yml"
ADDR=$(python3 $YPARSER $CFGPATH paudio_addr)
PORT=$(python3 $YPARSER $CFGPATH paudio_port)


if [[ ! $ADDR || ! PORT ]]; then
    echo ${BOLD}
    echo '(i) NOT found control TCP server address/port in `config.yml`,'
    echo '    using defaults `0.0.0.0:9990`'
    echo ${NORMAL}
    ADDR='0.0.0.0'
    PORT=9980
fi


if [[ $opc == *"-h"* ]]; then
    echo "usage:    paudio_server_restart.sh  [stop | --verbose]"
    echo ""
    echo "          stop            stops the server"
    echo "          -v --verbose    will keep messages to console,"
    echo "                          otherways will redirect to /dev/null"
    exit 0
fi


# Killing the running service:
server_is_runnnig=$(pgrep -fla "server.py paudio ")
if [[ ! $server_is_runnnig ]]; then
    echo "(i) pAudio server was not running."
fi

pkill -KILL -f "server.py paudio "
if [[ $opc == *'stop'* ]]; then
    exit 0
fi
sleep .25


# Re-launching the service.
# (i) It is IMPORTANT to redirect stdout & stderr to keep it alive even
#     if the launcher session has been closed (e.g. a crontab job),
#     except if -v --verbose is indicated
if [[ $opc == *"-v"* ]]; then
    echo "(i) RESTARTING pAudio server (VERBOSE MODE)"
    python3 "$SERVERPATH" "paudio" "$ADDR" "$PORT" -v &

else
    echo "(i) RESTARTING pAudio server (QUIET MODE redirected to /dev/null)"
    python3 "$SERVERPATH" "paudio" "$ADDR" "$PORT" >/dev/null 2>&1 &
fi
