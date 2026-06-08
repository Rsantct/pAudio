#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

#
# This script just provides:
#   - a Python venv if available
#   - a DBUS_SESSION_BUS_ADDRESS if neccessary for JACK when not in a X environment
#

PA_CFG_PATH=$HOME/pAudio/config/config.yml
WWW_CFG_PATH=$HOME/pAudio/code/share/www/public/config.json

LSPK=$(awk '/^loudspeaker:/ {print $2}' FS=': ' $PA_CFG_PATH)
rm -f $WWW_CFG_PATH
cat << EOF > $WWW_CFG_PATH
{
  "loudspeaker": "$LSPK"
}
EOF


BOLD="\033[1m"
RED="\033[0;31m"
BLUE="\033[0;34m"
GRAY="\033[0;90m"
NOCOLOR="\033[0m"


function start_www {

    if [[ $(pgrep -f "paudio_www.js") ]]; then
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) pAudio web server is already running."
        fi

    else
        rm -f $NODEJS_LOGERR
        node $HOME/pAudio/code/share/www/paudio_www.js 1>/dev/null 2>$NODEJS_LOGERR &
    fi
}


function start_ctrl {

    if [[ $(uname) == "Linux" ]]; then

        if [[ $(pgrep -f "server.py paudio_ctrl") ]]; then
            if [[ $VERBOSE == 'true' ]]; then
                echo "(paudio_restart) Restarting the paudio_ctrl server"
            fi
        fi

        pkill -f paudio_ctrl
        sleep .5
        python3 $HOME/pAudio/code/share/server.py paudio_ctrl 0.0.0.0 $CTRL_PORT 1>/dev/null 2>&1 &

    fi
}


function start_jack_mod {

    # needed for headless machines
    if [[ ! $DBUS_SESSION_BUS_ADDRESS ]]; then
        export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
    fi

    # needs & for background running
    if [[ $VERBOSE == 'true' ]]; then
        python3 $HOME/pAudio/code/share/jack_mod.py --prepare &

    else
        python3 $HOME/pAudio/code/share/jack_mod.py --prepare 1>/dev/null 2>&1 &

    fi

    sleep 1
}


function start_camilladsp {

    if [[ $(uname) == "Linux" ]]; then
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) killing CamillaDSP."
        fi
        pkill -KILL -f camilladsp 1>/dev/null 2>&1
        sleep 1
    fi

    if [[ $(pgrep camilladsp) ]]; then
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) CamillaDSP is already running."
        fi

    else
        if [[ $VERBOSE == 'true' ]]; then
            echo "(paudio_restart) Running CamillaDSP in wait mode ..."
        fi
        $HOME/bin/camilladsp --wait --mute \
            --address 127.0.0.1 --port $CAMILLADSP_PORT \
            --logfile $HOME/pAudio/log/camilladsp.log &
        sleep 2
    fi
}


function do_stop {

    python3 $HOME/pAudio/start.py stop                      # pAudio server

    if [[ $(uname) == "Linux" ]]; then
        pkill -KILL -f camilladsp 1>/dev/null 2>&1          # CamillaDSP
        sleep 1
        if [[ $KEEP_JACKD == 'false' ]]; then
            pkill -KILL -f 'jackd'    1>/dev/null 2>&1      # Jack
        fi

    elif [[ $(uname) == "Darwin" ]]; then
        $HOME/bin/paudio_launchagents.sh unload camilladsp  # CamillaDSP

    else
        echo "Only works on Linux or macOS"
        exit -1

    fi
    sleep 1
}


function do_start {

    if [[ $(uname) == "Linux" ]]; then
        start_www                                           # Node WWW server
        start_jack_mod                                      # Jack stuff includes loops
        start_camilladsp                                    # CamillaDSP
        start_ctrl                                          # pAudio control server

    elif [[ $(uname) == "Darwin" ]]; then
        $HOME/bin/paudio_launchagents.sh load camilladsp    # CamillaDSP

    else
        echo "Only works on Linux or macOS"
        exit -1
    fi

    if [[ $VERBOSE == 'true' ]]; then                       # pAudio server
        python3 $HOME/pAudio/start.py start -v &
    else
        python3 $HOME/pAudio/start.py start 1> $HOME/pAudio/log/start.log \
                                            2> $HOME/pAudio/log/start.err &
    fi

    # check for node js www server error log
    if [[ -s $NODEJS_LOGERR ]]; then
        echo -e ${RED}"ERROR loading web server, see pAudio/doc. Details: ""$NODEJS_LOGERR"${NOCOLOR}

    else
        if [[ $(pgrep -f "paudio_www.js") ]]; then
            echo -e ${GRAY}"(paudio_restart) pAudio web server is running :-)"${NOCOLOR}
        else
            echo -e ${RED}"(paudio_restart) pAudio web server NOT running :-/"${NOCOLOR}
        fi
    fi
}


# Python venv
if [[ ! $VIRTUAL_ENV ]]; then
    if [[ -f "$HOME/.env/bin/activate" ]]; then
        source $HOME/.env/bin/activate 1>/dev/null 2>&1
    fi
fi

# CamillaDSP port
CAMILLADSP_PORT=$(awk '/^camilladsp_port:/ {print $2}' FS=': ' $PA_CFG_PATH)
if [[ ! $CAMILLADSP_PORT ]]; then
    CAMILLADSP_PORT=1234
fi

# pAudio port
PA_PORT=$(awk '/^paudio_port:/ {print $2}' FS=': ' $PA_CFG_PATH)
if [[ ! $PA_PORT ]]; then
    PA_PORT=9990
fi
CTRL_PORT=$((PA_PORT + 1))

# node js web server error log
NODEJS_LOGERR=$HOME/pAudio/log/paudio_www.js.err

VERBOSE='false'
KEEP_JACKD='false'

# Main
if [[ $1 == 'stop' ]]; then
    do_stop

elif [[ ! $1 || $1 == *'start' ]]; then

    if [[ $2 == *'-v'* ]]; then
        VERBOSE='true'
    fi
    echo $VERBOSE > $HOME/pAudio/.verbose

    if [[ $3 == *'-kj'* ]]; then
        KEEP_JACKD='true'
    fi

    do_stop

    do_start

else
    echo
    echo "USAGE:   paudio_restart.sh  [ stop |  start [-v] [-kj] ]"
    echo "              -v   verbose mode"
    echo "              -kj  keep jackd server (developers can have a dummy backend for testing)"
    echo
fi
