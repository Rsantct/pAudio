#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

function help {

    echo
    echo "pAudio slave loudspeaker receiver"
    echo
    echo "Usage:    paudio_slave_lskp.sh  eth | wifi"
    echo
}


if [[ $1 ]]; then
    NET_LINK=$1
else
    help
    exit 0
fi


# set network addressing
if [ "$NET_LINK" = "eth" ]; then
    ZITA_BUFF=20
    LOCAL_IP="192.168.10.2"
    PAUDIO_IP="192.168.10.1"

elif [ "$NET_LINK" = "wifi" ]; then
    ZITA_BUFF=50
    LOCAL_IP="192.168.20.2"
    PAUDIO_IP="192.168.20.1"

else
    echo "(paudio_net_lspk) Bad NET_LINK '""$NET_LINK""' must be 'eth' or 'wifi'" >&2
    exit 1
fi

# stop
killall zita-n2j    1>/dev/null 2>&1
killall zita-j2n    1>/dev/null 2>&1
killall jackd       1>/dev/null 2>&1
sleep 1

# jack
echo "loading jack ..."
jackd -d alsa -P hw:Headphones,0 -o 2 -r 44100 -p 1024 -n 2 -z shaped --softmode --shorts \
1> /tmp/jackd.stdout 2> /tmp/jackd.stderr &
sleep 1

# zita receiver
echo "loading zita receiver ..."
zita-n2j --jname pAudio_recv --chan 1,2,3 --buff $ZITA_BUFF $LOCAL_IP 65000 \
1> /tmp/zita-n2j.stdout 2> /tmp/zita-n2j.stderr &
sleep 1

# zita sender
echo "loading zita sender ..."
zita-j2n --jname pAudio_send $PAUDIO_IP --16bit --chan 1 --ipv4 65000 \
1> /tmp/zita-j2n.stdout 2> /tmp/zita-j2n.stderr &
sleep 1

# wire jack
echo "wiring jack ..."
jack_connect   pAudio_recv:out_1    system:playback_1
jack_connect   pAudio_recv:out_2    system:playback_2
jack_connect   pAudio_recv:out_3    pAudio_send:in_1

#jack_lsp -c pAudio

echo
echo "(i) Logging jackd and zita under /tmp"
echo
