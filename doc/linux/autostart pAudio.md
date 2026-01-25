## autostart pAudio in a Desktop

You can put the provided file **`pAudio/doc/linux/.config/autostart/pAudio.desktop`** under your personal directory `~/.config/autostart/`

## autostart pAudio in a headless machine

You can use `/etc/rc.local`

    sleep 10 && su -l paudio -c "/home/paudio/bin/paudio_restart.sh" &

Or you can add a crontab job:

    @ reboot  su -l paudio -c "/home/paudio/bin/paudio_restart.sh" &
