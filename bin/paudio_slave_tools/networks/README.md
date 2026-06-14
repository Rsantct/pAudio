## Ensure usage of wlanX interfaces

After plugging an USB WiFi dongle **`wlan1`**, the OS can use it for your domestic WiFi in next reboots, example:

    $ nmcli connection show
    NAME                               UUID                                  TYPE      DEVICE 
    netplan-wlan0-MOVISTAR-WIFI6-3AC8  4eaa98c2-2c0a-3922-b266-32f01adff233  wifi      wlan1  
    ....


To keep domestic WiFi using **`wlan0`** (integrated):

- find your MAC, example:
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
    
    WIFINAME="netplan-wlan0-MOVISTAR-WIFI6-3AC8"
    MAC="b8:27:eb:83:c8:23"    # <---------- REPLACE WITH YOURS
    
    nmcli connwection modify "$WIFINAME" 802-11-wireless.mac-address "$MAC"
    nmcli connection modify "$WIFINAME" connection.interface-name wlan0
    
    nmcli connection down "$WIFINAME"
    nmcli connection up "$WIFINAME"
    ```


It should be ok now:

    $ nmcli connection show
    NAME                               UUID                                  TYPE      DEVICE 
    netplan-wlan0-MOVISTAR-WIFI6-3AC8  4eaa98c2-2c0a-3922-b266-32f01adff233  wifi      wlan0 

