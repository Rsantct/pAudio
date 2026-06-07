## Connecting to a NAS (samba)

Lets supose you have a samba shared disc available at `//192.168.1.46/p128`

**DO NOT** configure any kind of cifs mount under your **`/etc/fstab`**


## Prepare the mount point

    `mkdir -p /mnt/pinas`

## Prepare the samba connection credentials

In a secure place, for example under `/root/`

    /root/.pinas

        user=.....
        password=......

## Prepare systemd units

Please pay attention to set _YOURLOCALUSER_ below

#### `/etc/systemd/system/mnt-pinas.mount`

    [Unit]
    Description=Montaje samba de pinas
    After=network-online.target NetworkManager-wait-online.service
    Wants=network-online.target
    
    [Mount]
    What=//192.168.1.46/p128
    Where=/mnt/pinas
    Type=cifs
    Options=credentials=/root/.pinas,uid=YOURLOCALUSER,gid=YOURLOCALUSER,forceuid,forcegid,_netdev
    
    [Install]
    WantedBy=multi-user.target

#### `/etc/systemd/system/mnt-pinas.automount`

    [Unit]
    Description=Automontaje de pinas
    
    [Automount]
    Where=/mnt/pinas
    
    [Install]
    WantedBy=multi-user.target


## Enable ONLY automount

    sudo systemctl daemon-reload
    sudo systemctl enable mnt-pinas.automount
    sudo systemctl start mnt-pinas.automount

    
