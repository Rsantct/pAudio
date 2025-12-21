#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

# This program is called from the libresport --onevent option
#
# --onevent runs a program by providing some useful environmet variables:
#
#   PLAYER_EVENT, DURATION_MS, POSITION_MS, TRACK_ID, OLD_TRACK_ID, VOLUME
#
#   PLAYER_EVENT types:
#       preloading
#       started
#       playing
#       paused
#       changed
#       volume_set
#
# Binding ports to JACK is necessary because the libresport JACKAUDIO backend behavoir:
#   - The jack port does not emerge until first time playing.
#   - There is not any option to autoconnect to any destination jack port.

# Logging
LOG_PATH="$HOME/pAudio/log/librespot.log"
NOW_ZULU=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Event right padded
EVENT_RPAD=$(printf "%-12s" $PLAYER_EVENT)

# volume event
if [[ $PLAYER_EVENT == "volume_set" ]]; then
    echo $NOW_ZULU "$EVENT_RPAD" $VOLUME >> $LOG_PATH

# timed event
elif [[ $PLAYER_EVENT == "started" || $PLAYER_EVENT == "playing" || $PLAYER_EVENT == "paused" ]]; then
    echo $NOW_ZULU "$EVENT_RPAD" track:$TRACK_ID pos_ms:$POSITION_MS tot_ms:$DURATION_MS >> $LOG_PATH

# other events
else
    echo $NOW_ZULU "$EVENT_RPAD" track:$TRACK_ID >> $LOG_PATH

fi

# Binding Jack ports
if [[ $PLAYER_EVENT == "started" || $PLAYER_EVENT == "playing" || $PLAYER_EVENT == "changed" ]]; then

    conns=$(jack_lsp -c librespot_loop\:input)

    if [[ $conns && $conns != *"librespot:out"* ]]; then
        jack_connect librespot:out_0 librespot_loop:input_1 1>/dev/null 2>&1
        jack_connect librespot:out_1 librespot_loop:input_2 1>/dev/null 2>&1
    fi
fi
