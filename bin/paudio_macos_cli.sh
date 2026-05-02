#!/bin/bash

function help {
cat <<EOF

    Enviador de audio por LAN basado en JackTrip.

        Cambia la salida del escritorio a "BlackHole 2ch" y ejecuta JackTrip
        capturando el audio de BlackHole y enviándolo a la IP_REMOTA

    Uso:

        iniciar:    paudio_macos_cli.sh   IP_REMOTA
        detener:    paudio_macos_cli.sh   stop (restaura la salida de sonido del escritorio)

EOF
}


function get_RTAudioDEV {
    # Obtenemos el nombre del dispositivo RTAudio
    # del que capturaremos para enviar con JackTrip

    #   $ jacktrip --rtaudio --listdevices
    #   RTAudio: scanning devices...
    #   [CoreAudio - 129]: "BNQ: BenQ LCD" (0 ins, 2 outs)
    #   [CoreAudio - 130]: "Existential Audio Inc.: BlackHole 16ch" (16 ins, 16 outs)
    #   [CoreAudio - 131]: "Existential Audio Inc.: BlackHole 2ch" (2 ins, 2 outs)
    #   [CoreAudio - 132]: "Apple Inc.: MacBook Pro (micr?fono)" (1 ins, 0 outs)
    #   [CoreAudio - 133]: "Apple Inc.: MacBook Pro (altavoces)" (0 ins, 2 outs)

    jacktrip --rtaudio --listdevices | grep "$OUT_DEV" | sed -E 's/.*"([^"]+)".*/\1/'
}


function switch_macOS_output {
    # Conmutamos la salida de audio del Mac
    # (brew install switchudiosource-osx)
    tmp=$(SwitchAudioSource -a -t output | grep "$OUT_DEV")
    SwitchAudioSource -s "$tmp"
    sleep 0.5
    osascript -e "set volume output volume 100"
}


function restore_macOS_default_output {

    #   $ system_profiler SPAudioDataType | grep -B 10 "Default System Output Device: Yes"
    #             Default Input Device: Yes
    #             Input Channels: 1
    #             Manufacturer: Apple Inc.
    #             Current SampleRate: 48000
    #             Transport: Built-in
    #             Input Source: Micrófono del MacBook Pro
    #
    #           Altavoces del MacBook Pro:
    #                                                   OjO este linea puede que no aparezca
    #             Default Output Device: Yes        <<  si hay otro seleccionado actualmente
    #             Default System Output Device: Yes


    # Extraemos el nombre usando awk como máquina de estados
    local DEFAULT_OUT_DEV=$(system_profiler SPAudioDataType | awk '
        /^[[:space:]]+[^[:space:]].*:$/ {
            # Si la línea termina en ":" y tiene espacios al inicio, es un nombre de dispositivo
            # Limpiamos los espacios iniciales y el ":" final para guardarlo
            temp_name = $0;
            sub(/^[[:space:]]+/, "", temp_name);
            sub(/:$/, "", temp_name);
            device = temp_name;
        }
        /Default System Output Device: Yes/ {
            # Cuando encontramos la marca de salida de sistema, imprimimos el último dispositivo guardado
            print device;
            exit; # Salimos para evitar capturar otros si los hubiera
        }
    ')

    SwitchAudioSource -s "$DEFAULT_OUT_DEV"
    sleep 0.5
    osascript -e "set volume output volume 50"
}


function switch_remote_source {
    # Conmutamos la entrada en el FIRtro remoto.
    # OjO debe ser una source predefinida en el config.yml remoto
    echo 'Conmutando la fuente en el lado remoto ...'
    echo "source $1" | nc $REMOTE_IP 9990
    echo
}


function jacktrip_start {

    local remote_host=$1
    local RTAudioDEV=$(get_RTAudioDEV)
    local LOGPATH="$HOME"/pAudio/log/jacktrip_client_"$1"_"$(date "+%Y%m%d_%H%M%S")"".log"

    jacktrip --pingtoserver "$remote_host" --srate 44100 --bufsize 1024 \
        --bitres 16 --numchannels 2 \
        --remotename "$REMOTE_SRC_NAME" \
        --iostat 10 --iostatlog "$LOGPATH" \
        --rtaudio --audiodevice "$RTAudioDEV" &
}


if [[ $1 == *"-h"* || ! $1 ]]; then
    help
    exit 0
fi


killall jacktrip

if [[ $1 == *"stop"* ]]; then
    restore_macOS_default_output
    echo Bye
    exit 0
fi

# Se necesita recibir la IP remota como argumento, 'hostname.local' NO funciona
REMOTE_IP=$1

if ping -c 1 -W 1 $REMOTE_IP > /dev/null; then
    echo "Detectado host remoto "$REMOTE_IP
else
    echo "No hay respuesta de "$REMOTE_IP
    exit 0
fi


OUT_DEV='BlackHole 2ch'
REMOTE_SRC_NAME=$(system_profiler SPHardwareDataType | grep "Model Name" | awk -F: '{print $2}' | xargs)

jacktrip_start $REMOTE_IP

switch_macOS_output

switch_remote_source "$REMOTE_SRC_NAME"

exit 0

# Bucle de autoarranque
echo 'Iniciando bucle de auto arranque en caso de que se desconecte ...'
while true; do
    if [[ ! $(pgrep -fla "remotename $REMOTE_SRC_NAME") ]]; then
        echo "**************************************************"
        echo "Rearrancando cliente jacktrip con ""$REMOTE_IP""..."
        echo "**************************************************"
        start $REMOTE_IP
    fi
    sleep 10
done
