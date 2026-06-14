#!/bin/bash

########
# This will prompt you for the wifi password
########

# Configuración
MASTER_BSSID="08:BE:AC:03:38:A0"
CON_NAME="Enlace-Audio-Wifi"

# Asegurar máxima estabilidad en el driver Realtek del cliente
sudo iw dev wlan1 set power_save off

sudo nmcli connection delete "$CON_NAME" &>/dev/null

if [[ $1 == *'-q'* ]]; then
    echo "$CON_NAME has been removed"
    exit 0
fi

sudo nmcli connection add type wifi ifname wlan1 con-name "$CON_NAME" ssid "zitawifi" \
    802-11-wireless.mode infrastructure \
    802-11-wireless.bssid "$MASTER_BSSID" \
    ipv4.addresses 192.168.20.2/24 \
    ipv4.method manual \
    ipv4.never-default yes \
    802-11-wireless-security.key-mgmt wpa-psk \
    802-11-wireless-security.proto rsn \
    802-11-wireless-security.pairwise ccmp \
    802-11-wireless-security.group ccmp

sudo nmcli connection up "$CON_NAME" --ask
