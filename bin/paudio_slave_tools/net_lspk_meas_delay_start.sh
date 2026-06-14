#!/bin/bash

MINUTES=5
duration_sec=$(($MINUTES * 60))

LOG_PATH="/tmp/lspk_delay_info.log"
ERR_PATH="/tmp/lspk_delay_info.err"

killall jack_delay
sleep 1

if [[ $1 == *"-q"* ]]; then
    echo "jack_delay stopped."
    exit 0
fi

jack_delay -O right_lspk_send:in_3 -I right_lspk_recv:out_1 1>"$LOG_PATH" 2>"$ERR_PATH" &

echo "running jack_delay for "$MINUTES" minutes"

(sleep $duration_sec && \
killall jack_delay && \
echo "jack_delay stopped after "$MINUTES" minutes") &
