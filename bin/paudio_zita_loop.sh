#!/bin/bash

T_ANALISIS=30

function help {
    echo
    echo "Utilidad para evaluar el retardo y jitter entre dos servidores JACK unidos por ZITA-BRIDGE"
    echo
    echo "Uso:  paudio_zita_loop HOSTNAME.local BUFF [loop | delay]"
    echo "      paudio_zita_loop stop"
    echo
    echo "          HOSTNAME:   host colateral"
    echo "          BUFF:       valor obligatorio (ms)"
    echo "          loop:       para cablear el bucle de retorno en Jack"
    echo "          delay:      para medir el retardo y jitter del bucle con jack_delay por 30 s"
    echo "          stop:       detiene inmediatamente todos los procesos zita_loop"
    echo
    echo "Notas:    Los procesos zita_loop expirarán en 5 minutos automáticamente"
    echo "          Experimente probando valores de BUFF dependiendo de su conexión de red"
    echo
}


function comprueba_jack {

    if command -v jack_lsp &> /dev/null; then

        if jack_lsp &> /dev/null; then
            echo "JACK detectado ..."

        else
            echo "JACK no disponible, saliendo."
            exit 1
        fi

    else
        echo "JACK no disponible, saliendo."
        exit 1
    fi
}


colateral=$1

IP_REMOT=$(getent ahosts $colateral | awk 'NR==1{print $1}')
IP_LOCAL=$(ip route get 1.1.1.1 | grep -oP 'src \K\S+')
REM_ID="${IP_REMOT##*.}"
LOC_ID="${IP_LOCAL##*.}"

pkill -f "zita_loop_"
sleep 1

if [[ $1 == *"stop"* || $2 == *"stop"* ]]; then
    echo "stopped"
    exit 0

elif [[ ! $2 ]]; then
    help
    exit 0

elif [[ $2 == *"h"* ]]; then
    help
    exit 0

else
    comprueba_jack

    BUFF=$2

    # La IP siempre es la receptora
    # y el sufijo del puerto jack es el de la IP del colateral

    # envía
    zita-j2n --jname zita_loop_j2n_$REM_ID              $IP_REMOT 630$LOC_ID &
    # recibe
    zita-n2j --jname zita_loop_n2j_$REM_ID --buff $BUFF $IP_LOCAL 630$REM_ID &

    # bucle de retorno
    if [[ $3 == "loop" ]]; then
        echo "CABLEANDO BUCLE EN JACK ..."
        sleep 3
        jack_connect    zita_loop_n2j_$REM_ID:out_1  zita_loop_j2n_$REM_ID:in_1
        jack_connect    zita_loop_n2j_$REM_ID:out_2  zita_loop_j2n_$REM_ID:in_2

    # medidor jack_delay por 30 segundos
    elif [[ $3 == "delay" ]]; then

        sleep 5
        echo "*** ESPERE 30 SEGUNDOS PARA ESTABILIZAR ***"
        sleep 25

        echo "MIDIENDO EL RETARDO DURANTE "$T_ANALISIS" s..."
        # el resultado se vuelca a /tmp
        rm -f /tmp/jack_delay
        jack_delay -O zita_loop_j2n_$REM_ID:in_1 -I zita_loop_n2j_$REM_ID:out_1 > /tmp/jack_delay &
        sleep .2
        # y se muestra con tail -f
        tail -f /tmp/jack_delay &
        sleep $T_ANALISIS
        killall jack_delay

        # análisis
        echo
        python3 $HOME/bin/paudio_slave_tools/net_lspk_jitter_stats.py /tmp/jack_delay
        echo
    fi

    # Programar la terminación de zita_loops en 5 minutos en segundo plano desvinculado
    (sleep 300 && pkill -f zita_loop) >/dev/null 2>&1 &
    disown
    echo "*** Los procesos zita_loop expirarán en 5 minutos automáticamente ***"
    exit 0

fi
