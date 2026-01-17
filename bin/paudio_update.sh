#!/bin/bash

function update_camilladsp_plist {

    # Update CamillaDSP port if set under config.yml

    CAMILLADSP_PORT=$(awk '/^camilladsp_port:/ {print $2}' FS=': ' $HOME/pAudio/config.yml)
    if [[ ! $CAMILLADSP_PORT ]]; then
        CAMILLADSP_PORT=1234
    fi

    old="--port 1234"
    new="--port "$CAMILLADSP_PORT
    fname=$HOME"/Library/LaunchAgents/com.pAudio.camilladsp.plist"

    sed -i '' "s|$old|$new|g" "$fname"
}


GITSITE=Rsantct

echo
read -p "Enter the branch (intro to 'master'): " ans
if [[ ! $ans ]];then
    BRANCH="master"
else
    BRANCH=$ans
fi

echo
read -p "Upgrading from 'https://github.com/"$GITSITE"/pAudio/"$BRANCH"'.  It's ok? (y/N): " ans
if [[ $ans != *"y"*  && $ans != *"Y"* ]];then
    echo 'Bye!'
    exit 0
fi


cd
mkdir -p ~/tmp

cd ~/tmp
rm -rf pAudio-$BRANCH
wget https://github.com/Rsantct/pAudio/archive/$BRANCH.zip
unzip $BRANCH.zip
rm -f $BRANCH.zip

cd

# Backup config
cp ~/pAudio/config.yml ~/pAudio/config.yml.BAK 1>/dev/null 2>&1

# Copy all stuff
cp -r ~/tmp/pAudio-$BRANCH/pAudio  ~/
cp    ~/tmp/pAudio-$BRANCH/bin/*   ~/bin/
chmod +x ~/bin/paudio*
chmod +x ~/pAudio/start*
chmod +x ~/pAudio/code/share/plugins/*

# Restore config
cp ~/pAudio/config.yml.BAK ~/pAudio/config.yml 1>/dev/null 2>&1

# Stop the server, CamillaDSP, www and control
pkill -f "server.py paudio "        1>/dev/null 2>&1
pkill -f "camilladsp"               1>/dev/null 2>&1
pkill -f "nodejs_www_server"        1>/dev/null 2>&1
pkill -f "server.py paudio_ctrl"    1>/dev/null 2>&1

echo

if [[ $(uname) == "Darwin" ]]; then
    echo "Updating pAudio .plist files to ~/Library/LaunchAgents/"
    cp pAudio/code/share/macOS/com.pAudio.* ~/Library/LaunchAgents/
    update_camilladsp_plist
fi

echo
echo "Done, restarting pAudio ..."
echo

# Restart pAudio
~/bin/paudio_restart.sh
