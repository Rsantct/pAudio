# Install

## MacOS

- [BlackHole](https://github.com/ExistentialAudio/BlackHole#installation-instructions) to route your audio.

- [Node.js](https://nodejs.org/en) to serve the control web page (Choose the recommended `LTS` version).

- [Apple Xcode](https://developer.apple.com/xcode/) Command Line Tools (this includes the [git](https://git-scm.com) tool).

### recommended

In order to automatically switch the Mac system-wide audio playback to the pAudio BlackHole input, and restore later, you may want to install a couple of additional tools:

- [AdjustVolume](https://github.com/jonomuller/device-volume-adjuster)
- [SwitchAudioSource](https://github.com/deweller/switchaudio-osx)

## Linux
TO BE DONE


## CamillaDSP

[CamillaDSP](https://github.com/HEnquist/camilladsp#readme) is a powerful audio processing tool.

CamillaDSP is provided as a single executable binary. Proceed as follow:

- Prepare a `~/bin` folder under your home directory: `makedir -p ~/bin`, or make the new folder by using the File Manager.

- Go to https://github.com/HEnquist/camilladsp/releases.

- Choose **`amd64`** for Intel CPU or **`aarch64`** for Apple CPU, download the **`Latest`** version.

- Doubleclick to the downloaded `.tar` file to uncompress it. 

- Move the extracted binary **`camilladsp`** to your **`~/bin`** folder.

## Python modules

[pip](https://pip.pypa.io/en/stable/) is the standard Python package manager.

Upgrade `pip`:

    python3 -m pip install --upgrade pip setuptools wheel

If the above command fails, you'll need to [install pip](https://pip.pypa.io/en/stable/installation/#supported-methods), then retry in order to upgrade `setuptools`.

Install standard Python modules:

    pip3 install numpy scipy matplotlib PyYAML watchdog sounddevice websocket_client


Install the CamillaDSP module:

    pip3 install git+https://github.com/HEnquist/pycamilladsp.git


## The pAudio application

**pAudio** is given in a folder to be located under your HOME directory.

Download or clone this repo, unzip, then copy the **`paudio`** folder to your home directory.

Make the launcher to be executable: `chmod +x ~/paudio/paudio.sh`

# Settings

You don't have to worry about preparing CamillaDSP configuration files.

All settings are done inside **`paudio/config.yml`**

## Sound Device

Set the output device name to use in **`~/paudio/config.yml`**, for example:

    output:
        device:      E30 II      # DAC USB Topping E30

#### MacOS

Find the proper device name in **Midi and Audio Setup**, the one your loudspeakers are connected.

You can also check device names by running:

    system_profiler $( system_profiler -listDataTypes | grep Audio)

#### Linux
TO BE DONE


## Loudspeaker

Prepare a loudspeaker folder, no matter if an empty one.

    mkdir ~/paudio/loudspeakeres/MyLspkName/

Then set **`~/paudio/config.yml`**

    # Loudspeaker in use
    loudspeaker:    MyLspkName

## DRC-FIR (optional)

Simply drop your DRC FIR files under the loudspeaker folder.

        paudio/loudspeakeres/MyLspkName/
            drc.L.setName.pcm
            drc.R.setName.pcm


# Run / Stop pAudio

To run the system-wide processor:

    ~/paudio/paudio.sh   start

To stop: 

    ~/paudio/paudio.sh   stop


# Controlling pAudio

    http://localhost:8088

<img src="./img/pAudio%20web%20-20dB.png" width="500"><img src="./img/pAudio%20web%200dB.png" width="500">

