# Install

## MacOS

You need [BlackHole](https://github.com/ExistentialAudio/BlackHole#installation-instructions) to route your audio.

You also need [Node.js](https://nodejs.org/en) to serve the control web page.

## CamillaDSP

Go to https://github.com/HEnquist/camilladsp/releases, download current, unzip and leave the binary under your **`~/bin`** folder.

## Python modules

    pip3 install numpy scipy matplotlib yaml watchdog sounddevice

## pAudio

Download or clone this repo, unzip, then copy the **`paudio`** folder to your **`~/bin`** folder.

Also copy the provided `bin/` scripts to your **`~/bin`** folder.

# Settings

## DRC-FIR

Prepare a loudspeaker folder with your DRC files:

        paudio/loudspeakeres/lspkName/
            drc.L.setName.pcm
            drc.R.setName.pcm

Set the sound device and `lspkName` in `~/paudio/config.yml`

## Sound Device

Find the proper device name in **Midi and Audio Setup**

Set the device name in `~/paudio/config.yml`

# Running

    ~/bin/paudio.sh start

# Control

    http://localhost:8088

<img src="./img/pAudio%20web.png" width="500">

