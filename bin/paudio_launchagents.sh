#!/bin/bash

function do_launch {

    if [[ $arg2 == 'cam'* ]]; then
        launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.camilladsp.plist  2>/dev/null

    else
        launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.ctrl.plist        2>/dev/null
        launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.www.plist         2>/dev/null
        launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.camilladsp.plist  2>/dev/null

    fi
}


# Only for MacOS
SO=$(uname)
if [[ $SO != "Darwin" ]]; then
    echo "This is only for MacOS, to manage pAudio '.plist' agents"
    echo
    exit 0
fi


# arguments to lower case
arg1=$(echo "$1" | tr '[:upper:]' '[:lower:]')
arg2=$(echo "$2" | tr '[:upper:]' '[:lower:]')


if [[ $arg1 == 'off' || $arg1 == 'unload' || $arg1 == 'stop' ]]; then

    mode='unload'
    do_launch

elif [[ $arg1 == 'on' || $arg1 == 'load' || $arg1 == 'start' ]]; then

    mode='load'
    do_launch

elif [[ $arg1 == 'reload' || $arg1 == 'restart' ]]; then

    mode='unload'
    do_launch
    sleep 1
    mode='load'
    do_launch

else
    echo
    echo "Usage: paudio_launchagents.sh   load | unload | reload  [camilladsp]"
    echo ""
    echo "                                with 'camilladsp' skip others"
    echo
fi

# List state
echo "Loaded agents (ctrl, www, camilladsp):"
launchctl list | grep pAudio
