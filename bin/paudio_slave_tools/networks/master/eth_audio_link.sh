#!/bin/bash

# ipv4.never-default yes: never changes the default gateway to here. Regular traffic will flow through by WiFi
# 'connection add' has NOT 'ipv4.gateway', this way it makes a private link without external output.
# nmcli makes this parmanent after robooting.


# Delete old
sudo nmcli connection delete "Enlace-Audio-Eth" &>/dev/null

# Create new
sudo nmcli connection add type ethernet ifname eth0 \
    con-name "Enlace-Audio-Eth" \
    ipv4.addresses 192.168.10.1/24 \
    ipv4.method manual

# Avoid default gw (internet)
sudo nmcli connection modify "Enlace-Audio-Eth" ipv4.never-default yes

# Ignore ipv6 to avoid unnecessary discovering traffic
sudo nmcli connection modify "Enlace-Audio-Eth" ipv6.method ignore

# Up
sudo nmcli connection up "Enlace-Audio-Eth"
