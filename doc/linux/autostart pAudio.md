## autostart pAudio in a Desktop

You can put the provided file **`pAudio/doc/linux/.config/autostart/pAudio.desktop`** under your personal directory `~/.config/autostart/`

## autostart pAudio in a headless machine

--- Legacy method, you can use `/etc/rc.local`

    sleep 10 && su -l paudio -c "/home/paudio/bin/paudio_restart.sh" &

--- Or you can add a crontab job:

    @ reboot  su -l paudio -c "/home/paudio/bin/paudio_restart.sh" &

--- Or you can prepare a Systemd service unit:

```
sudo nano /etc/systemd/system/paudio.service
```
    
```
[Unit]
Description=pAudio servers launcher (1x Node - www, 2x python backend, 1x Jack, 1x CamillaDSP)
# Network ready
After=network-online.target
Wants=network-online.target

# Retries limit
StartLimitBurst=1
StartLimitIntervalSec=60

[Service]
User=paudio
Group=paudio
WorkingDirectory=/home/paudio
ExecStart=/home/paudio/bin/paudio_restart.sh start

# Will launch other processes in background
Type=forking

# When paudio_restart.sh finishes, the remaining started processes should remain active.
RemainAfterExit=yes

# Restart the service if 'failed'
Restart=on-failure
# a time to release ports
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable paudio.service
sudo systemctl start paudio.service
sudo systemctl status paudio.service
```
