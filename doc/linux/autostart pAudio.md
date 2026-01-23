## autostart pAudio in a Desktop

You can use the provided **`~/config/autostart/pAudio.desktop`** file

## autostart pAudio in a headless machine

You can use `/etc/rc.local`

    sleep 10 && su -l paudio -c "/home/paudio/bin/paudio_restart.sh" &

Or you can add a crontab job:

    @ reboot  su -l paudio -c "/home/paudio/bin/paudio_restart.sh" &
