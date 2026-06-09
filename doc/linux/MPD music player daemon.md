# MPD

MPD is used to play

- music files
- internet streams
- CD audio

## Install

MPC and GMPC are basic MPC clients (terminal and graphical)

    sudo apt install mpd mpc gmpc

We use our own mpd session, please, after installing MPD, check that the global service is not enabled (recent versions does not):

    pi@rpi3wl-l:/home/paudio $ sudo systemctl status mpd.service 
    ○ mpd.service - Music Player Daemon
         Loaded: loaded (/usr/lib/systemd/system/mpd.service; disabled; preset: enabled)
         Active: inactive (dead)
           Docs: man:mpd(1)
                 man:mpd.conf(5)
                 file:///usr/share/doc/mpd/html/user.html
    pi@rpi3wl-l:/home/paudio $ sudo systemctl status mpd.socket
    ○ mpd.socket
         Loaded: loaded (/usr/lib/systemd/system/mpd.socket; disabled; preset: enabled)
         Active: inactive (dead)
       Triggers: ● mpd.service
         Listen: /run/mpd/socket (Stream)
                 [::]:6600 (Stream)

If enabled, please disable both of them.

## Prepare pAudio to use MPD

Under **`pAudio/config/config.yml`**

    
    jack:
    
        device:         hw:mysoundcard,0
        ...
        ...

        sources:
    
            ...
            ...
            
            mpd:
                jport:  mpd_loop    # this is an internal default, here for clariy
                lu_offset: 6
    
            iRadio:
                jport:  mpd_loop
    
    
    plugins:
        ...
        - mpd.py
    
