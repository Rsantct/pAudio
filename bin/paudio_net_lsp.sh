#!/bin/bash

BUFF=50

IP_PAUDIO='192.168.1.70'
IP_LOCAL=$(ip route get 1 | awk '{print $(NF-2); exit}')

# stop
killall zita-n2j
killall zita-j2n
killall jackd
sleep 1

# jack
jackd -d alsa -P hw:Headphones,0 -o 2 -r 44100 -p 1024 -n 2 -z shaped --softmode --shorts &
sleep 1

# zita receiver
zita-n2j --jname pAudio_recv --buff $BUFF $IP_LOCAL 65000 &
sleep 1

# zita sender
zita-j2n --jname pAudio_send $IP_PAUDIO --16bit --chan 2 --ipv4 65000 &
sleep 1

# wire jack
jack_connect   pAudio_recv:out_1    system:playback_1
jack_connect   pAudio_recv:out_2    system:playback_2
jack_connect   pAudio_recv:out_1    pAudio_send:in_1
jack_connect   pAudio_recv:out_2    pAudio_send:in_2

jack_lsp -c pAudio
