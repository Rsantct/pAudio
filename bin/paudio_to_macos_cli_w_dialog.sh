#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

# A network audio receiver for Coreaudio macOS from a pAudio system,
# based on JackTrip.

# The 'dialog' command needs to be installed:
#   https://github.com/swiftDialog

# CONFIGURE HERE the pAudio sender IP
REMOTE_IP=192.168.1.41  # kef c35

# Constants
# JackTrip defaults are 4464 and 61002, we use here non standard
BIND_PORT=4466
UDP_PORT=63002

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


# -- begin ---

# Mecanismo toggle: si ya está enviando lo detiene
if pgrep -f "bindport $BIND_PORT" 1>/dev/null ; then

    if ! confirma "¿STOP Jacktrip sender and receiver?"; then
        echo "quit:" >> "$CMD_FILE" # no espera 5 segundos
        exit 0
    fi

    # Iniciamos ventana de progreso
    dialog \
      --title "pAudio  --  x  -->  macOS" \
      --commandfile "$CMD_FILE" &

    # Terminate any local JackTrip instance if it is running.
    do_log "Stopping ..."
    pkill -KILL -f "bindport $BIND_PORT" #1>/dev/null 2>&1
    sleep .2

    # FIN
    end_log
    exit 0

else

    if ! confirma "¿START receiving from $REMOTE_IP?"; then
        echo "quit:" >> "$CMD_FILE" # no espera 5 segundos
        exit 0
    fi
fi

# Iniciamos ventana de progreso
dialog \
  --title "pAudio  -------->  macOS" \
  --commandfile "$CMD_FILE" &

# Retrieves audio parameters from the sender.
read -r FS BUF <<< $(echo "ctrl jack_get_params" | nc $REMOTE_IP 9990)
echo "remote info: samplerate "$FS", buffer "$BUF


# Start the local JackTrip receiver.
echo "local: start the local JackTrip receiver"
jacktrip    --rtaudio -q 8 -r 2 \
            --bindport "$BIND_PORT" \
            --peerport "$BIND_PORT" \
            --udpbaseport "$UDP_PORT" \
            --srate $FS --bufsize "$BUF" \
            --receivechannels 2 -c "$REMOTE_IP" 1>/dev/null 2>&1 &


# Restart the remote JackTrip sender.
echo "remote: restart JackTrip sender"
echo "ctrl jacktrip_sender_restart" | nc "$REMOTE_IP" 9990 1>/dev/null 2>&1
sleep 1
echo "ctrl jacktrip_sender_connect" | nc "$REMOTE_IP" 9990 1>/dev/null 2>&1
