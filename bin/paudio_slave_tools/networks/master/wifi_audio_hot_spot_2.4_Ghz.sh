#!/bin/bash

# Choose the better channel on your zone
CH=13

# Configuración de contraseña (mínimo 8 caracteres)
PASSWORD="xxxxxxxxxxxxxx"

CON_NAME="Enlace-Audio-Wifi"

sudo nmcli connection delete "$CON_NAME" &>/dev/null

if [[ $1 == *'-q'* ]]; then
    echo "$CON_NAME"" has been removed"
    exit 0
fi

# ancho 20 MHz más inmunidad radioeléctrica
sudo nmcli connection add type wifi ifname wlan1 con-name "$CON_NAME" ssid "zitawifi" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
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
