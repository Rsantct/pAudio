# Connecting to a shared disc (samba)

**DO NOT** configure any kind of mount under your **`/etc/fstab`**

## Prepare systemd units for automount to remotes shared

Prepare mount point

    mkdir -p /mnt/mynas

Prepare samba connection credentials, for example under /root

    /root/.mynas

        user=.....
        password=......


Prepare two system units, the mount itself and the automount.

`/etc/systemd/system/mnt-pinas.mount`

    [Unit]
    Description=Mount my NAS
    After=network-online.target
    Wants=network-online.target
    
    [Mount]
    What=//192.168.1.xxx/SHARED_NAME
    Where=/mnt/mynas
    Type=cifs
    Options=credentials=/root/.mynas,uid=YOUR_LOCAL_USER_HERE,gid=YOUR_LOCAL_USER_HERE,forceuid,forcegid,_netdev
    
    [Install]
    WantedBy=multi-user.target

`sudo nano /etc/systemd/system/mnt-pinas.automount`

    [Unit]
    Description=Automontaje CIFS pinas
    After=network-online.target
    Wants=network-online.target

    [Automount]
    Where=/mnt/pinas
    
    [Install]
    WantedBy=multi-user.target
