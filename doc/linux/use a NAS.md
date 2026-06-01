## Connecting to a NAS (samba)

**DO NOT** configure any kind of cifs mount under your **`/etc/fstab`**


## Prepare systemd units

The systemd units will help you to automount remotes shared

- Prepare mount point

    `mkdir -p /mnt/mynas`

- Prepare samba connection credentials, in a secure place, for example under /root

```
    /root/.mynas

        user=.....
        password=......
```

- Prepare two systemd units, the mount itself and the automount:

**`/etc/systemd/system/mnt-mynas.mount`**

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

**`sudo nano /etc/systemd/system/mnt-mynas.automount`**

    [Unit]
    Description=Automount my NAS
    After=network-online.target
    Wants=network-online.target

    [Automount]
    Where=/mnt/mynas
    
    [Install]
    WantedBy=multi-user.target

- Enable both
    ```
    sudo systemctl enable mnt-mynas.mount
    sudo systemctl enable mnt-mynas.automount
    sudo systemctl start mnt-mynas.automount
    ```

