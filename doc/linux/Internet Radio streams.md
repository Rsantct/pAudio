# Streaming internet radio

Here we have some radio stations using .m3u8 streams

We use MPD (Music Player Daemon), pleaase refer to MPD.md

## Configure presets

Use the file **`pAudio/config/istreams`**, example:

    RNE:                https://rtvelivestream.rtve.es/rtvesec/rne/rne_r1_main.m3u8
    Radio Clasica:      https://rtvelivestream.rtve.es/rtvesec/rne/rne_r2_main.m3u8
    Radio 3:            https://rtvelivestream.rtve.es/rtvesec/rne/rne_r3_main.m3u8

## Play a station

Prepare a simple macro (bash script), for example **`pAudio/macros/01_RNE`**

    #!/bin/bash
    
    STATION="RNE"
    
    python3 $HOME/pAudio/macros/templates/play_m3u8.py "$STATION"  &
    paudio_control input iRadio
    paudio_control lu_offset 12

This will appear as a button in the control web page
