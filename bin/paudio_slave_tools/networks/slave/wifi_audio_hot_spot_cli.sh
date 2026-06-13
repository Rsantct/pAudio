#!/bin/bash

echo "Desactivando wlan1 en NetworkManager..."
sudo nmcli device set wlan1 managed no

# Limpieza total de procesos y IPs previas
sudo killall wpa_supplicant &>/dev/null
sudo ip addr flush dev wlan1

echo "Reiniciando interfaz física wlan1..."
sudo ip link set wlan1 down
sleep 1
sudo ip link set wlan1 up
sleep 1

echo "Forzando asociación directa a la red abierta 'AudioPrivateNet'..."
# Configuramos la tarjeta por hardware sin intermediarios
sudo iwconfig wlan1 mode Managed
sudo iwconfig wlan1 enc off
sudo iwconfig wlan1 essid AudioPrivateNet

echo "Esperando estabilización de la radio..."
sleep 3

echo "Configurando IP estática 192.168.20.2..."
sudo ip addr add 192.168.20.2/24 dev wlan1

echo "Verificando conectividad con RPI_A..."
if ping -c 3 -w 4 192.168.20.1 > /dev/null; then
    echo "--------------------------------------------------"
    echo " ¡ENLACE DE AUDIO INALÁMBRICO ESTABLECIDO CON ÉXITO!"
    echo "--------------------------------------------------"
    iwconfig wlan1 | grep -E "(ESSID|Access Point)"
else
    echo "--- DIAGNÓSTICO ---"
    echo "Estado de iwconfig wlan1:"
    iwconfig wlan1
fi

