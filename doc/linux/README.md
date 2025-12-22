# pAudio under Linux

This is for a black box Linux machine (say a little Raspberry Pi 3B+ and up), or even a Desktop machine.


## Install Linux Packages


### Generic tools and control web page software:

    sudo apt install alsa-utils alsa-ucm-conf xdotool cdtool libportaudio2 libffi-dev git nodejs node-js-yaml

### Python packages from Debian:

    sudo apt install python3-venv python3-pip python3-dev python3-yaml python3-jack-client \
         python3-mpd python3-pydbus python3-numpy python3-scipy python3-matplotlib \
         python3-pyudev python3-libdiscid python3-musicbrainzngs python3-watchdog \
         python3-serial python3-m3u8 python3-psutil python3-websocket python3-pydbus 


### Python packages not provided by Debian:

`sounddevice`, `pycamilladsp`, `discid`

You need to prepare a Python Virtual Environment for your user (by inheriting the system Python packages)

```
$ python3 -m venv --system-site-packages ~/.env
$ source ~/.env/bin/activate
(.env) $ pip3 install sounddevice
(.env) $ pip3 install git+https://github.com/HEnquist/pycamilladsp.git
(.env) $ pip3 install discid

You can now deactivate the Python Env BUT it is not necessary

(.env) $ deactivate
$
```

## Install CamillaDSP with the JACK backend

CamillaDSP pre-built binaries comes with Coreaudio, Pulseaudio and ALSA, but for JACK you'll need to compile it.

NOTE: do not need `sudo`, just complite under your pAudio regular Linux user.

### Get the RUST compiler

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

### Get the CamillaDSP source code

https://github.com/HEnquist/camilladsp/releases

### Install compiler dependencies

    sudo apt-get install pkg-config libasound2-dev openssl libssl-dev \
                 jackd2 libjack-jackd2-dev

### Compile

    RUSTFLAGS='-C target-feature=+neon -C target-cpu=native' \
    cargo build --release --features jack-backend

MORE INFO [here](https://github.com/HEnquist/camilladsp/tree/master?tab=readme-ov-file#building)

## Configure pAudio

When using JACK, please see **`doc/config_examples`**

MORE INFO [here](https://github.com/HEnquist/camilladsp/tree/master?tab=readme-ov-file#jack) 
