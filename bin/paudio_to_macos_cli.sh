#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

# A network audio receiver for Coreaudio macOS from a pAudio system,
# based on JackTrip.


# CONFIGURE HERE the pAudio sender IP
REMOTE_IP=192.168.1.41  # kef c35


# JackTrip defaults are 4464 and 61002, we use here non standard
BIND_PORT=4466
UDP_PORT=63002


# Terminate any local JackTrip instance if it is running.
pkill -KILL -f "bindport $BIND_PORT"
sleep .2


# Exiting if 'stop' was given
if [[ $1 == 'stop' ]]; then

    echo "stopping JackTrip sender and receiver"
    echo "ctrl jacktrip_sender_restart stop" | nc "$REMOTE_IP" 9990 1>/dev/null 2>&1
    exit 0
fi


# Retrieves audio parameters from the sender.
read -r FS BUF <<< $(echo "ctrl jack_get_params" | nc $REMOTE_IP 9990)
echo "remote info: samplerate "$FS", buffer "$BUF


# Start the local JackTrip receiver.
echo "local: start the local JackTrip receiver"
jacktrip    --rtaudio -q 8 -r 2 \
            --bindport "$BIND_PORT" \
            --peerport "$BIND_PORT" \
            --udpbaseport "$UDP_PORT" \
            --srate $FS --bufsize "$BUF" \
            --receivechannels 2 -c "$REMOTE_IP" 1>/dev/null 2>&1 &


# Restart the remote JackTrip sender.
echo "remote: restart JackTrip sender"
echo "ctrl jacktrip_sender_restart" | nc "$REMOTE_IP" 9990 1>/dev/null 2>&1
sleep 1
echo "ctrl jacktrip_sender_connect" | nc "$REMOTE_IP" 9990 1>/dev/null 2>&1
