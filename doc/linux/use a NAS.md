## Connecting to a NAS (samba)

**DO NOT** configure any kind of cifs mount under your **`/etc/fstab`**


## Prepare the mount point

    `mkdir -p /mnt/mynas`

## Prepare the samba connection credentials

In a secure place, for example under `/root/`

    /root/.mynas

        user=.....
        password=......

## Prepare systemd units

#### `/etc/systemd/system/mnt-mynas.mount`

    [Unit]
    Description=Montaje CIFS pinas
    After=network-online.target NetworkManager-wait-online.service
    Wants=network-online.target
    
    [Mount]
    What=//192.168.1.46/p128
    Where=/mnt/pinas
    Type=cifs
    Options=credentials=/root/.pinas,uid=rafax,gid=rafax,forceuid,forcegid,_netdev
    
    [Install]
    WantedBy=multi-user.target

#### `/etc/systemd/system/mnt-mynas.automount`

    [Unit]
    Description=Automontaje CIFS pinas
    
    [Automount]
    Where=/mnt/pinas
    
    [Install]
    WantedBy=multi-user.target


## Enable ONLY automount

    sudo systemctl daemon-reload
    sudo systemctl enable mnt-mynas.automount
    sudo systemctl start mnt-mynas.automount

    
