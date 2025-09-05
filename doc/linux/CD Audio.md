## Playing CD

To enable CD playing, configure as below inside `config.yml`

    jack:
        ...
        ...
        sources:
            ...
            ...
            cd:
                jpname:     mpd_loop

    cdrom_device:  /dev/cdrom

    plugins:
        - autoplay_cdda.py
        - autoeject_cdda.py


## Fine tuning Mplayer (OBSOLETE)

NOTE: before 2024-11 CD playback was in charge of Mplayer, **currently CD playback works with MPD**.

On slow machines you may need to fine tune the Mplayer cache, see `~/.mplayer/config.sample`


## Apple SuperDrive on Linux

CREDITS: https://cmos.blog/use-apples-usb-superdrive-with-linux/


Apple Superdrive prevents to run on not Apple machines :-/, but you can unlock this behavior :-)

Lets suppose your drive is attached on /dev/sr0, if not sure see your dmesg.

- Install package `sg3-utils`

    ```
    $ sudo apt-get install sg3-utils
    ```

- Try to enable the drive manually:

    ```
    $ sg_raw /dev/sr0 EA 00 00 00 00 00 01
    NVMe Result=0x0
    ```

Now, you can insert a CD.

- Automatic enabling by udev rules:

    ```
    $ sudo nano /etc/udev/rules.d/60-Apple-Superdrive.rules
    ```

    ```
    # Initialise Apple SuperDrive
    ACTION=="add", ATTRS{idProduct}=="1500", ATTRS{idVendor}=="05ac", DRIVERS=="usb", RUN+="/usr/bin/sg_raw /dev/$kernel EA 00 00 00 00 00 01"
    ```

- A crontab job to ensure the disc is ejected at the end of the day:

    ```
    # eject Apple SuperDrives because no tray eject button
    30 01 *  *  *    eject /dev/sr0
    30 01 *  *  *    eject /dev/sr1
    ```

### Link to /dev/cdrom

If you have more than one CR-ROM unit, you may want to ensure `/dev/cdrom` points to your SuperDrive.

As this is a system setup, you need to add a task to the `crontab` of `root`:

    # m h  dom mon dow   command    
    @reboot /home/YOUR_USER_HERE/bin/apple_superdrive.py link


