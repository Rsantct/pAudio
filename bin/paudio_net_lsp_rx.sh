#!/bin/bash

# stop
killall zita-n2j
killall jackd
sleep 1

# jack
jackd -d alsa -P hw:Headphones,0 -o 2 -r 44100 -p 1024 -n 2 -z shaped --softmode --shorts &
sleep 1

# zita receiver
IP_LOCAL=$(ip route get 1 | awk '{print $(NF-2); exit}')
zita-n2j --jname pAudio --buff 95 "$IP_LOCAL" 65000 &
sleep 1

# wire jack
jack_connect   pAudio:out_1    system:playback_1
jack_connect   pAudio:out_2    system:playback_2

jack_lsp -c pAudio
