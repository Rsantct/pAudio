#!/bin/bash

# The 'dialog' command needs to be installed:
#   https://github.com/swiftDialog
#


# Constantes
OUT_DEV='BlackHole 2ch'

read -r -d '' AYUDA << 'EOF'

    Enviador de audio para macOS, a un sistema pAudio remoto basado en JackTrip.

    Cambia la salida de audio del Mac a "BlackHole 2ch" y ejecuta JackTrip
    capturando el audio de BlackHole y enviándolo al host remoto indicado
    en el archivo de configuración, ejemplo:

        ~/bin/paudio_macos_cli.conf

            remote = mi_dsp_host.local    (o dirección IP)

    NOTA: el Mac debe disponer de las utilidades siguientes (ver documentación pAudio)
        - JackTrip
        - BlackHole
        - AdjustVolume
        - SwitchAudioSource

EOF
AYUDA_HTML=$(printf '%s\n' "$AYUDA" | sed 's/$/<br>/' | tr -d '\n')


# Archivo para volcar los mensajes que muestra la ventana de progreso
CMD_FILE="/var/tmp/paudio_macos_cli.log"
rm -f "$CMD_FILE"


function aviso {
    MENSAJE=$1
    osascript -e "display dialog \"$MENSAJE\" buttons {\"OK\"} default button \"OK\" with title \"Información\""
}


function confirma {
    MENSAJE=$1
    respuesta=$(osascript -e "display dialog \"$MENSAJE\" buttons {\"No\", \"Sí\"} default button \"Sí\" with title \"JackTrip\"")

    if [[ "$respuesta" == *"button returned:Sí"* ]]; then
        return 0
    else
        return 1
    fi
}


function do_log {
    echo "$1"
    echo "message: +<br>""$1" >> "$CMD_FILE"
}


function end_log {
    sleep 3
    echo "quit:" >> "$CMD_FILE"
}


function help {
    echo "$AYUDA"
    echo "message: +<br>""$AYUDA_HTML" > "$CMD_FILE"
}


function is_integer {

    # regular expression para comprobar si $1 es entero
    [[ "$1" =~ ^-?[0-9]+$ ]]
}


function get_ip {
    # Obtiene la IP a partir de un host

    if is_integer $1; then
        echo $1
        return 0
    fi

    host=$1

    # Ejecuta un solo ping y extrae la IP de los paréntesis
    IP=$(ping -c 1 "$host" | head -1 | cut -d '(' -f 2 | cut -d ')' -f 1)

    if [[ $IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo $IP
    else
        echo ''
    fi
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

    /usr/local/bin/jacktrip --rtaudio --listdevices | grep "$OUT_DEV" | sed -E 's/.*"([^"]+)".*/\1/'
}


function switch_macOS_output {
    # Conmutamos la salida de audio del Mac
    # (brew install switchudiosource-osx)

    tmp=$(/opt/homebrew/bin/SwitchAudioSource -a -t output | grep "$OUT_DEV")
    /opt/homebrew/bin/SwitchAudioSource -s "$tmp"
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

    do_log "Restaurando el audio en el Mac ..."
    osascript -e "set volume output volume 25"
    sleep 0.5
    /opt/homebrew/bin/SwitchAudioSource -s "$DEFAULT_OUT_DEV"

}


function switch_remote_source {

    local src=$1

    # Conmutamos la entrada en el FIRtro remoto.
    # OjO debe ser una source predefinida en el config.yml remoto
    do_log 'Conmutando la fuente en el lado remoto ...'
    echo "source $src" | nc $REMOTE 9990
    echo
}


function get_remote_samplerate {

    local samplerate=44100
    local tmp=''

    # Consultamos la samplerate del host remoto
    tmp=$(echo "state" | nc $REMOTE 9990 | grep "samplerate" | sed 's/.*: //;s/,//')
    if is_integer $tmp; then
        samplerate=$tmp
    fi

    echo $samplerate
}


function get_remote_jack_buffer {

    local jack_period=1024
    local tmp=''

    # Consultamos el jack_period del host remoto
    tmp=$(echo "state" | nc $REMOTE 9990 | grep "jack_period" | sed 's/.*: //;s/,//')
    if is_integer $tmp; then
        jack_period=$tmp
    fi

    echo $jack_period
}


function jacktrip_start {

    local srate=$(get_remote_samplerate)
    local buffer=$(get_remote_jack_buffer)


    do_log "Iniciando el envío con JackTrip ..."

    mkdir -p "$HOME"/tmp

    local RTAudioDEV=$(get_RTAudioDEV)
    local LOGPATH="$HOME""/tmp/jacktrip_client.log"
    local STATSPATH="$HOME""/tmp/jacktrip_client.stats"

    /usr/local/bin/jacktrip --pingtoserver "$REMOTE" \
        --udprt \
        --bufsize "$buffer" \
        --queue "$QUEUE" \
        --redundancy "$REDUNDANCY" \
        --numchannels 2 \
        --remotename "$REMOTE_SRC_NAME" \
        --iostat 10 --iostatlog "$STATSPATH" \
        --rtaudio --audiodevice "$RTAudioDEV" \
        --srate "$srate" \
        1>"$LOGPATH" 2>&1 &
}


function load_conf {

    local this_path=$(readlink -f "$0")
    CONFPATH="${this_path%.sh}.conf"

    QUEUE=3
    REDUNDANCY=1

    if [[ ! -f "$CONFPATH" ]]; then
        do_log "Falta archivo de configuración ""$CONFPATH"
        end_log
        exit 0
    fi

    # Lee cualquier sintaxis, ejemplos:
    #   remote = 'mi_pc.local'
    #   REMOTO: mi_pc.local

    REMOTE_IP_OR_NAME=$( grep -Ei '^[[:space:]]*(remote|remoto)' $CONFPATH | \
        head -n 1 | sed -E 's/^[[:space:]]*(remote|remoto)[[:space:]]*[:=][[:space:]]*//I' | \
        sed 's/["'\'']//g' | \
        xargs )

    QUEUE=$( grep -Ei '^[[:space:]]*(queue)' $CONFPATH | \
        head -n 1 | sed -E 's/^[[:space:]]*(queue)[[:space:]]*[:=][[:space:]]*//I' | \
        sed 's/["'\'']//g' | \
        xargs )

    REDUNDANCY=$( grep -Ei '^[[:space:]]*(redundancy)' $CONFPATH | \
        head -n 1 | sed -E 's/^[[:space:]]*(redundancy)[[:space:]]*[:=][[:space:]]*//I' | \
        sed 's/["'\'']//g' | \
        xargs )
}


function is_valid_ip {

    local ip=$1

    # Definición de la expresión regular para IPv4 (0-255 en cada octeto)
    local regex="^(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$"

    if [[ $ip =~ $regex ]]; then
        return 0 # ok
    else
        return 1 # bad
    fi
}


# Ayuda
if [[ $1 == *"-h"* ]]; then
    help
    exit 0
fi


# ----- INICIO ------

# Lee el archivo de configuración
load_conf


# Se necesita la IP remota, direcciones 'xxxx.local' no funcionan
REMOTE=$(get_ip $REMOTE_IP_OR_NAME)


if [[ $REMOTE != *"."* ]]; then
    do_log "$REMOTE_IP_OR_NAME"" NO responde"
    end_log
    exit 1
fi


# Mecanismo toggle: si ya está enviando lo detiene
if pgrep -f jacktrip 1>/dev/null ; then

    if ! confirma "¿DETENER el envío de audio al remoto?"; then
        echo "quit:" >> "$CMD_FILE" # no espera 5 segundos
        exit 0
    fi

    # Iniciamos ventana de progreso
    dialog \
      --title "macOS --x--> pAudio" \
      --commandfile "$CMD_FILE" &

    # Detiene JackTrip
    do_log "Deteniendo el envío JackTrip ..."
    killall jacktrip 1>/dev/null 2>&1

    # Restaura la salida de audio del Mac
    restore_macOS_default_output

    # FIN
    end_log
    exit 0

else

    if ! confirma "¿INICIAR el envío de audio a $REMOTE?"; then
        echo "quit:" >> "$CMD_FILE" # no espera 5 segundos
        exit 0
    fi
fi


# Iniciamos ventana de progreso
dialog \
  --title "macOS ----> pAudio" \
  --commandfile "$CMD_FILE" &


# Comprobamos comunicación con el Host Remoto
if ! is_valid_ip $REMOTE; then
    do_log "Host remoto no válido."
    end_log
    exit 1
fi

if ping -c 1 -W 1 $REMOTE > /dev/null; then
    do_log "Detectado host remoto ""$REMOTE"

else
    do_log "No hay respuesta de ""$REMOTE"
    end_log
    exit 0
fi


# Variables
REMOTE_SRC_NAME=$(system_profiler SPHardwareDataType | grep "Model Name" | awk -F: '{print $2}' | xargs)

# Iniciamos el cliente JackTrip
jacktrip_start

# Enviamos el audio a BlaclHole > JackTrip > Host_Remoto
switch_macOS_output

# Ordenamos al Host Remoto que seleccione la fuente de nuestro JackTrip
switch_remote_source "$REMOTE_SRC_NAME"

end_log
