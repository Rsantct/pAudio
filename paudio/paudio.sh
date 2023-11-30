#!/bin/bash

function help {
    echo
    echo "  Usage:  paudio.sh   stop | start [ -v ]"
    echo "          -v:  verbose mode not detached from terminal"
    echo
}


function stop_all {
    pkill -f "paudio\/code\/"
    echo "pAudio has been stopped."
}


if [[ $1 = *"stop"* ]]; then

    # Stop all (audio and web page)
    stop_all

    echo "Restoring previous Default Playback Device"
    dev=$(cat ~/paudio/.previous_default_device)
    SwitchAudioSource -s "$dev"

    echo "Restoring previous Playback Device Volume"
    vol=$(cat ~/paudio/.previous_default_device_volume)
    osascript -e 'set volume output volume '$vol

    exit 0


elif [[ $1 = *"start"* ]]; then

    # Stop all (audio and web page)
    stop_all

    # Control web page
    node ~/paudio/code/share/www/nodejs_www_server/www-server.js >/dev/null 2>&1 &
    echo "pAudio web server running in background ..."

    # Audio in verbose mode
    if [[ $2 = *"-v"* ]]; then
        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 -v
        pkill -f "paudio/code/share/www/nodejs"

    # Audio in silent mode
    else
        python3 ~/paudio/code/share/server.py paudio 0.0.0.0 9990 1>/dev/null 2>&1 &
        echo "pAudio running in background ..."

    fi


else

    help


fi

