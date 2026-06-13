## ensure usage of WiFi wlanXX interfaces

To keep domestic WiFi using `wlan0` (integrated) and Audio WiFi using `wlan1` (usb dongle)

Please copy these files to 

    /etc/systemd/network/10-wlan0-builtin.link
    /etc/systemd/network/11-wlan1-usb.link
