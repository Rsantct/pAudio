# pAudio under Linux

This is for a black box Linux machine (say a little Raspberry Pi 3B+ and up), or even a Desktop machine.


## Install Linux Packages

The control web page needs:

    sudo apt install git nodejs node-js-yaml

### Python packages from Debian:

    sudo apt install python3-numpy python3-scipy python3-matplotlib \
             python3-yaml python3-jack-client python3-watchdog \
             python3-websocket

### Python packages not provided by Debian:

`sounddevice` and `pycamilladsp`

You need to prepare a Python Virtual Environment for your user (by inheriting the system Python packages)

```
$ python3 -m venv --system-site-packages ~/.env
$ source ~/.env/bin/activate
(.env) $ pip3 install sounddevice
(.env) $ pip3 install git+https://github.com/HEnquist/pycamilladsp.git

You can now deactivate the Python Env BUT it is not necessary

(.env) $ deactivate
$
```

## Install CamillaDSP with the JACK backend

CamillaDSP pre-built binaries comes with Coreaudio, Pulseaudio and ALSA, but for JACK you'll need to compile it.

NOTE: do not need `sudo`, just complite under your pAudio regular Linux user.

### Get the RUST compiler

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

### Install compiler dependencies

    sudo apt-get install pkg-config libasound2-dev openssl libssl-dev \
                 jackd2 libjack-jackd2-dev

### Compile

    RUSTFLAGS='-C target-feature=+neon -C target-cpu=native' \
    cargo build --release --features jack-backend

MORE INFO [here](https://github.com/HEnquist/camilladsp/tree/master?tab=readme-ov-file#building)

## Configure pAudio

When using JACK you need to configure something like this, please see **`doc/config_examples`**


    # Sound server
    sound_server:       jack
    jack:
            device:     hw:0,0
            period:     1024
            nperiods:   2
    
    # Audio devices (these are for CamillaDSP to use JACK)
    input:
        device:         default
        format:         FLOAT32LE
    
    output:
        device:         default
        format:         FLOAT32LE

MORE INFO [here](https://github.com/HEnquist/camilladsp/tree/master?tab=readme-ov-file#jack) 
