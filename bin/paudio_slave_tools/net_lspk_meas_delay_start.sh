#!/bin/bash

MINUTES=$1

if [[ ! $MINUTES ]]; then
    echo
    echo "    usage:    net_lspk_meas_delay_start.sh  N  (minutes)"
    echo
    exit 0
fi

# kill others but not me
pkill --older 1 -f "meas_delay"
pkill -f jack_delay

duration_sec=$(($MINUTES * 60))

LOG_PATH="/tmp/lspk_delay_info.log"
ERR_PATH="/tmp/lspk_delay_info.err"


if [[ $1 == *"-q"* ]]; then
    exit 0
fi

jack_delay -O right_lspk_send:in_3 -I right_lspk_recv:out_1 1>"$LOG_PATH" 2>"$ERR_PATH" &

echo "running jack_delay for "$MINUTES" minutes"

# timer in background to kill jack_delay
(sleep $duration_sec && \
killall jack_delay 1>/dev/null && \
echo "jack_delay stopped after "$MINUTES" minutes") &
