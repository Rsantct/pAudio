#!/bin/bash

SO=$(uname)

if [[ $SO != "Darwin" ]]; then
    echo "This is only for MacOS, to manage pAudio '.plist' agents"
    echo
    exit 0
fi

if [[ $1 ]]; then

    mode=$1
    launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.ctrl.plist
    launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.www.plist
    launchctl $mode $HOME/Library/LaunchAgents/com.pAudio.camilladsp.plist

else
    echo "Usage: paudio_launch.sh   load | unload"
    echo
fi

echo "List of pAudio agents:"
echo
launchctl list | grep pAudio
