# macOS advanced: audio sources

## - Basic setup

Listen to **Mac Desktop sound** (Spotify, Safari web browser, Music, ...) through by the pAudio processor.

#### macOS:

    Settings ---> Sound Output --> BlackHole 2Ch

pAudio does this automatically on startup, also restores your previous Sound Output when stopped.

#### pAudio:
    
    pAudio/config/config.yml
        coreaudio:
            devices:
                capture:    BlackHole 2Ch
                playback:   Line Out (or whatever sound card output for your loudspeakers)


## - Combined setup

For example if you have a TV connected to OPTICAL LINE IN on your old 2014 model Mac Mini, and you want not to take care of selecting the source:
- Mac Desktop sound
- TV sound (optical noise free)

#### macOS MIDI Audio Configuration:

You need to prepare an **Aggregate Device** under _MIDI Audio Configuration_, having both BlackHole and your Line In, example:

<img src="./img/mac%20os%20aggregate%20audio%20device.png" width="800">

This example is a MacBook Pro without Line In, but an USB sound card with line input doing the same.

**NOTICE:**

If you use your integrated Mac Line IN / OUT connections, set the **Source Clock** to Line In, this way **Drif correction** will be applied to the BlackHole device.

#### macOs:

    Settings ---> Sound Output --> Aggregate Device

#### pAudio:
    
    pAudio/config/config.yml
        coreaudio:
            devices:
                capture:    Aggregate Device
                playback:   Line Out (or whatever sound card output for your loudspeakers)

## - Advanced setup: source selection

pAudio will select one of:
- Mac Desktop sound
- Line In (example: a TV)

Example for TV input on an external USB sound card and main output through by the integrated Mac audio sound output

    coreaudio:

        devices:

            capture:

                Mac Desktop:
                    channels: 2
                    device: BlackHole 2ch

                TV:
                    channels: 2
                    device: "USB Audio CODEC "    # this card name includes a weird trailing space
    
            playback:

                channels: 2
                device: Altavoces del MacBook Pro
