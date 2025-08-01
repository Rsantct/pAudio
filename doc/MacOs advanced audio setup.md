# MacOS: advanced audio sources

## Basic setup

Listen to **MacOs Desktop sounds** (Spotify, Safari web browser, Music, ...) through by the pAudio processor.

#### MacOs:

    Settings ---> Sound Output --> BlackHole 2Ch

#### pAudio:
    
    pAudio/config.yml
        coreaudio:
            devices:
                capture:    BlackHole 2Ch
                playback:   Line Out (or whatever sound card output for your loudspeakers)


## Combined setup

For example if you have a TV connected to Line In on your Mac, and you want not to take care of selecting the source:
- **Mac desktop** sound
- **TV** sound

#### MacOS:

You need to prepare an **Aggregate Device** under _MIDI Audio Configuration_, having both BlackHole and your Line In, example:

<img src="./img/nac%20os%20aggregate%20audio%29device.png" width="500"><img src="./img/pAudio%20web%200dB.png" width="500">

This example MacBook Pro has no Line In, but an USB sound card with line input doing the same.


If you have Line In on your Mac and also you use your Mac Line Out for your loudspekeUse the proper Line In available on your system.


    Settings ---> Sound Output --> Aggregate Device


