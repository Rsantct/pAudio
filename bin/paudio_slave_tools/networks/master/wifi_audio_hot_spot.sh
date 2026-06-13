#!/bin/bash

sudo nmcli connection delete "Enlace-Audio-Wifi" &>/dev/null

if [[ $1 == *'-q'* ]]; then
    echo "Enlace-Audio-Wifi has been removed"
    exit 0
fi

# Creamos el AP totalmente ABIERTO (sin claves) en 2.4 GHz
sudo nmcli connection add type wifi ifname wlan1 con-name "Enlace-Audio-Wifi" ssid "AudioPrivateNet" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    802-11-wireless.channel 1 \
    ipv4.addresses 192.168.20.1/24 \
    ipv4.method manual \
    ipv4.never-default yes

sudo nmcli connection up "Enlace-Audio-Wifi"

