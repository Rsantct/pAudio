# Install

## MacOS

You need [BlackHole](https://github.com/ExistentialAudio/BlackHole#installation-instructions) to route your audio.

You also need [Node.js](https://nodejs.org/en) to serve the control web page.

## CamillaDSP

Prepare a `~/bin` folder under your home directory: `makedir -p ~/bin`, or use Finder.

Go to https://github.com/HEnquist/camilladsp/releases, download **Latest**. Use _amd64_ for Intel CPU or _aarch64_ for Apple CPU.

Doubleclick to the `.tar` file to uncompress it. Then move the extracted binary to your **`~/bin`** folder.

## Python modules

Standard modules

    python3 -m pip install --upgrade pip
    pip3 install numpy scipy matplotlib PyYAML watchdog sounddevice websocket_client

The CamillaDSP module

    cd ~/Downloads
    git clone https://github.com/HEnquist/pycamilladsp.git
    cd pycamilladsp
    pip3 install .


## The pAudio application

**pAudio** is given in a folder to be located under your HOME directory.

Download or clone this repo, unzip, then copy the **`paudio`** folder to your home directory.

Make the launcher to be executable: `chmod +x ~/paudio/paudio.sh`

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

    ~/paudio/paudio.sh start

# Control

    http://localhost:8088

<img src="./img/pAudio%20web%20-20dB.png" width="500"><img src="./img/pAudio%20web%200dB.png" width="500">

