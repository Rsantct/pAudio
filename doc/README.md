# Install needed audio software on MacOS

- [BlackHole](https://github.com/ExistentialAudio/BlackHole#installation-instructions) to route your audio.

- [Node.js](https://nodejs.org/en) to serve the control web page (Choose the recommended `LTS` version).

- [Apple Xcode](https://developer.apple.com/xcode/) Command Line Tools (this includes the [git](https://git-scm.com) tool).

## recommended

In order to automatically switch the Mac system-wide audio playback to the pAudio BlackHole input, and restore later, you may want to install a couple of additional tools:

- [AdjustVolume](https://github.com/jonomuller/device-volume-adjuster)
- [SwitchAudioSource](https://github.com/deweller/switchaudio-osx)

## CamillaDSP

[CamillaDSP](https://github.com/HEnquist/camilladsp#readme) is a powerful audio processing tool.

CamillaDSP is provided as a single executable binary. Proceed as follow:

- Prepare a `~/bin` folder under your home directory: `makedir -p ~/bin`, or make the new folder by using the File Manager.

- Go to https://github.com/HEnquist/camilladsp/releases.

- Choose **`amd64`** for Intel CPU or **`aarch64`** for Apple CPU, download the **`Latest`** version.

- Doubleclick to the downloaded `.tar` file to uncompress it.

- Move the extracted binary **`camilladsp`** to your **`~/bin`** folder.


If the binary was downloaded using Safari, then macOS most likely won't allow it to be executed. Trying will result in an error message such as:

    "camilladsp" can't be opened because its integrity cannot be verified.

The solution is to remove the "quarantine" attribute from the binary using the xattr command.

Open a a terminal and run:

    xattr -d com.apple.quarantine /path/to/camilladsp


## Python modules

NOTE: needs Python >= 3.10

[pip](https://pip.pypa.io/en/stable/) is the standard Python package manager.

Upgrade `pip`:

    python3 -m pip install --upgrade pip setuptools wheel

If the above command fails, you'll need to [install pip](https://pip.pypa.io/en/stable/installation/#supported-methods), then retry in order to upgrade `setuptools`.

Install standard Python modules:

    pip3 install numpy scipy matplotlib PyYAML watchdog sounddevice websocket_client


Install the CamillaDSP python module:

    pip3 install git+https://github.com/HEnquist/pycamilladsp.git


# Install needed audio software on Linux

see `Linux.md`

# Install the pAudio application

**pAudio** is given in a folder to be located under your HOME directory.

You need to download or clone this repo, unzip, then copy the **`pAudio`** folder to your home directory.

**The easy way:** just get the script **`bin/paudio_update.sh`** into your `bin/` folder and run it:

    mkdir -p ~/bin
    wget -O ~/bin/paudio_update.sh https://raw.githubusercontent.com/Rsantct/pAudio/master/bin/paudio_update.sh
    bash ~/bin/paudio_update.sh


# Settings

You don't have to worry about preparing CamillaDSP configuration files.

All settings are done inside **`pAudio/config.yml`**

## Sound Device

Set the output device name to be used in **`~/pAudio/config.yml`**, for example:

    output:
        device:      E30 II      # DAC USB Topping E30

#### MacOS

Find the proper device name in **Midi and Audio Setup**, the one your loudspeakers are connected.

You can also check device names by running:

    system_profiler $( system_profiler -listDataTypes | grep Audio)

#### Linux

See `Linux.md`

## recommended: Digital Room Correction DRC-FIR

Simply drop your DRC FIR files under the loudspeaker folder.

        pAudio/loudspeakeres/MyLspkName/
            drc.L.setName.pcm
            drc.R.setName.pcm

DRC tools:

 - [Rsantct/DRC](https://github.com/Rsantct/DRC)
 - [rripio/DSC](https://github.com/rripio/DSC)
 - Room EQ Wizard


## optional: PEQ parametric equalizer

Just prepare a PEQ section inside `pAudio/config.yml`, see the given example file.


## optional: Active loudspeaker FIR filtering: driver EQ and XOVER

You may want to apply FIR filtering to your loudspeaker.

To do so, prepare your FIR files and drop them under the loudspeaker folder.

See the provided `/loudspeakers/examples` for more details.

Some XOVER FIR design tools:

 - [rePhase](https://rephase.org) very good, but only for Windows :-/
 - [rripio/DSD](https://github.com/rripio/DSD)

More resources [here](https://www.minidsp.com/applications/advanced-tools/fir-filter-tools)

# Run / Stop pAudio

To run the system-wide processor:

    ~/pAudio/start.py   start

To stop:

    ~/pAudio/start.py   stop


# Controlling pAudio

    http://localhost:8088

See here the loudness compensation curve for 20 dB below your reference SPL (volume 0 dB). It includes a 3 dB boost due to the target curve.

<img src="./img/pAudio%20web%20-20dB.png" width="500"><img src="./img/pAudio%20web%200dB.png" width="500">

