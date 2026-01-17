#!/bin/bash

function do_launch {
    launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.ctrl.plist        2>/dev/null
    launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.www.plist         2>/dev/null
    launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.camilladsp.plist  2>/dev/null
}


# Only for MacOS
SO=$(uname)
if [[ $SO != "Darwin" ]]; then
    echo "This is only for MacOS, to manage pAudio '.plist' agents"
    echo
    exit 0
fi


# argument to lower case
arg=$(echo "$1" | tr '[:upper:]' '[:lower:]')

if [[ $arg == 'off' || $arg == 'unload' || $arg == 'stop' ]]; then

    mode='unload'
    do_launch

elif [[ $arg == 'on' || $arg == 'load' || $arg == 'start' ]]; then

    mode='load'
    do_launch

elif [[ $arg == 'reload' || $arg == 'restart' ]]; then

    mode='unload'
    do_launch
    sleep 1
    mode='load'
    do_launch

else
    echo
    echo "Usage: paudio_launch.sh   load | unload | reload"
    echo
fi

# List state
echo "List of pAudio agents (ctrl, www, camilladsp):"
echo
launchctl list | grep pAudio
