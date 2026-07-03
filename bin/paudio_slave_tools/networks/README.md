## Overview

We want to have a **dedicated network link for audio packets** (zita-njbridge)

Use the provided scripts under master / slave folders

### Wired Ethernet

This is preferred

### Wifi

Wifi can work if you assume some secure buffering therefore some audio latency.

- Better to operate in **5 Ghz** band and non DFS channel (for example ch 36).
- 2.4Ghz can work as well with stable 1 ms ping latencies 

    ```
    # first 7 ms because power saving chipset wake up process
    # but zita UDP continuous usage will avoid that.
    
    pi@rpi3wl-l:~ $ ping -i 0.005 -c 100 192.168.20.2
    PING 192.168.20.2 (192.168.20.2) 56(84) bytes of data.
    64 bytes from 192.168.20.2: icmp_seq=1 ttl=64 time=7.75 ms
    64 bytes from 192.168.20.2: icmp_seq=2 ttl=64 time=1.35 ms
    64 bytes from 192.168.20.2: icmp_seq=3 ttl=64 time=1.48 ms
    64 bytes from 192.168.20.2: icmp_seq=4 ttl=64 time=1.47 ms
    64 bytes from 192.168.20.2: icmp_seq=5 ttl=64 time=1.32 ms
    64 bytes from 192.168.20.2: icmp_seq=6 ttl=64 time=1.37 ms
    64 bytes from 192.168.20.2: icmp_seq=7 ttl=64 time=1.32 ms
    64 bytes from 192.168.20.2: icmp_seq=8 ttl=64 time=1.39 ms
    64 bytes from 192.168.20.2: icmp_seq=9 ttl=64 time=1.39 ms
    64 bytes from 192.168.20.2: icmp_seq=10 ttl=64 time=1.30 ms
    ...
    ...
    64 bytes from 192.168.20.2: icmp_seq=98 ttl=64 time=1.08 ms
    64 bytes from 192.168.20.2: icmp_seq=99 ttl=64 time=1.09 ms
    64 bytes from 192.168.20.2: icmp_seq=100 ttl=64 time=1.33 ms
    
    --- 192.168.20.2 ping statistics ---
    100 packets transmitted, 100 received, 0% packet loss, time 497ms
    rtt min/avg/max/mdev = 1.064/1.218/7.751/0.664 ms
    ```

## Static usage of wlan interfaces

After plugging an USB WiFi dongle **`wlan1`**, the OS can use it for your domestic WiFi in next reboots, example:

    $ nmcli connection show
    NAME                               UUID                                  TYPE      DEVICE 
    netplan-wlan0-MOVISTAR-WIFI6-3AC8  4eaa98c2-2c0a-3922-b266-32f01adff233  wifi      wlan1  
    ....


To keep domestic WiFi using an specific wireless interface, for example the one of your integrated chipset:

- find your integrated MAC, example:
    ```
    $ ifconfig wlan0
    wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            inet 192.168.1.70  netmask 255.255.255.0  broadcast 192.168.1.255
            inet6 fe80::ba27:ebff:fe83:c823  prefixlen 64  scopeid 0x20<link>
            ether b8:27:eb:83:c8:23
    ```

- run the following script as **`sudo`**

    ```
    #!/bin/bash

    # *** Replace values with yours: ***
    WLAN_ID="wlan0"
    WIFINAME="netplan-wlan0-MOVISTAR-WIFI6-3AC8"
    MAC="b8:27:eb:83:c8:23"
    
    nmcli connwection modify "$WIFINAME" 802-11-wireless.mac-address "$MAC"
    nmcli connection modify "$WIFINAME" connection.interface-name "$WLAN_ID"
    nmcli connection down "$WIFINAME"
    nmcli connection up "$WIFINAME"
    ```


Check devices MAC usage with:

    $ nmcli connection show
    $ iwconfig
    $ ifconfig
