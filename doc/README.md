# Install

## MacOS

You need [BlackHole](https://github.com/ExistentialAudio/BlackHole#installation-instructions) to route your audio.

You also need [Node.js](https://nodejs.org/en) to serve the control web page.

## CamillaDSP

Prepare a `~/bin` folder under your home directory: `makedir -p ~/bin`.

Go to https://github.com/HEnquist/camilladsp/releases, download **Latest**. Use _amd64_ for Intel CPU or _aarch64_ for Apple CPU.

Uncompress and move the binary to your **`~/bin`** folder.

## Python modules

    pip3 install numpy scipy matplotlib PyYAML watchdog sounddevice

## pAudio

Download or clone this repo, unzip, then copy the **`paudio`** folder to your home directory.

Also copy the provided `bin/paudio.....` scripts to your **`~/bin`** folder.

Make them executable: `chmod +x ~/bin/paudio*`

# Settings

## DRC-FIR

Prepare a loudspeaker folder with your DRC files:

        paudio/loudspeakeres/lspkName/
            drc.L.setName.pcm
            drc.R.setName.pcm

Set the `lspkName` in `~/paudio/config.yml`

## Sound Device

Find the proper device name in **Midi and Audio Setup**

Set the device name in `~/paudio/config.yml`

# Running

    ~/bin/paudio.sh start

# Control

    http://localhost:8088

<img src="./img/pAudio%20web.png" width="500">

