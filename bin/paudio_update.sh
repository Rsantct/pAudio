#!/bin/bash

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

# Restore config
cp ~/pAudio/config.yml.BAK ~/pAudio/config.yml 1>/dev/null 2>&1

# Stop any paudio backend
pkill -f "server.py paudio "        1>/dev/null 2>&1
pkill -f "camilladsp"               1>/dev/null 2>&1

echo

if [[ $(uname) == "Darwin" ]]; then

    read -p "Do you want to add [pAudio] to your macOS session? (y/N): " ans
    if [[ $ans == *"y"*  || $ans == *"Y"* ]];then
        cp pAudio/code/share/macOS/com.pAudio.* ~/Library/LaunchAgents/
        echo "pAudio plist files copied to "$HOME"/Library/LaunchAgents/"
    fi

fi

echo
echo "Done, bye!"
