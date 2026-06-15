#!/bin/bash

# The first channel of the 5 GHz low band, free of DFS penalties
# and with excellent stability for transmitting consecutive audio frames
CH=36

WLAN_ID="wlan0"

# Configuración de contraseña (mínimo 8 caracteres)
PASSWORD="xxxxxxxxx"

CON_NAME="Enlace-Audio-Wifi"

sudo nmcli connection delete "$CON_NAME" &>/dev/null

if [[ $1 == *'-q'* ]]; then
    echo "$CON_NAME"" has been removed"
    exit 0
fi


# Configuración AP en 5 GHz para enlace de audio dedicado
sudo nmcli connection add type wifi ifname "$WLAN_ID" con-name "$CON_NAME" ssid "zitawifi" \
    802-11-wireless.mode ap \
    802-11-wireless.band a \
    802-11-wireless.channel $CH \
    802-11-wireless.channel-width 20 \
    ipv4.addresses 192.168.20.1/24 \
    ipv4.method manual \
    ipv4.never-default yes \
    802-11-wireless-security.key-mgmt wpa-psk \
    802-11-wireless-security.psk "$PASSWORD" \
    802-11-wireless-security.proto rsn \
    802-11-wireless-security.pairwise ccmp \
    802-11-wireless-security.group ccmp


sudo nmcli connection up "$CON_NAME"
