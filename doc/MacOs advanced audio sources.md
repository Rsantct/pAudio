# MacOS: advanced audio sources

## - Basic setup

Listen to **Mac Desktop sound** (Spotify, Safari web browser, Music, ...) through by the pAudio processor.

#### MacOs:

    Settings ---> Sound Output --> BlackHole 2Ch

#### pAudio:
    
    pAudio/config.yml
        coreaudio:
            devices:
                capture:    BlackHole 2Ch
                playback:   Line Out (or whatever sound card output for your loudspeakers)


## - Combined setup

For example if you have a TV connected to Line In on your Mac, and you want not to take care of selecting the source:
- Mac Desktop sound
- TV sound

#### MacOS MIDI Audio Configuration:

You need to prepare an **Aggregate Device** under _MIDI Audio Configuration_, having both BlackHole and your Line In, example:

<img src="./img/mac%20os%20aggregate%20audio%20device.png" width="800">

This example is a MacBook Pro without Line In, but an USB sound card with line input doing the same.

**NOTICE:**

If you use your integrated Mac Line IN / OUT connections, set the **Source Clock** to Line In, this way **Drif correction** will be applied to the BlackHole device.

#### MacOs:

    Settings ---> Sound Output --> Aggregate Device

#### pAudio:
    
    pAudio/config.yml
        coreaudio:
            devices:
                capture:    Aggregate Device
                playback:   Line Out (or whatever sound card output for your loudspeakers)

## - Advanced setup: source selection

pAudio will select one of:
- Mac Desktop sound
- Line In (example: a TV)

See below, normal and alternative source selection syntax are shown:

    coreaudio:

        devices:

            capture:

                ---------------------------------------------------------------
                Normal coreaudio input device directly specified:

                channels: 2
                device: BlackHole 2ch
                format: FLOAT32LE


                ---------------------------------------------------------------
                Alternative more than one section, to have source selection

                Mac Desktop:
                    channels: 2
                    device: BlackHole 2ch
                    format: FLOAT32LE

                TV:
                    channels: 2
                    device: UMC204HD 192k
                    format: S24LE
                ---------------------------------------------------------------


            playback:

                channels: 2
                device: Altavoces del MacBook Pro
                format: FLOAT32LE
