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
cp -r ~/tmp/pAudio-$BRANCH/pAudio  ~/
cp    ~/tmp/pAudio-$BRANCH/bin/*   ~/bin/

chmod +x ~/bin/paudio*
chmod +x ~/pAudio/start.sh

# Restore config
cp ~/pAudio/config.yml.BAK ~/pAudio/config.yml 1>/dev/null 2>&1

echo "Done, bye!"
