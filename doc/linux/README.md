# pAudio under Linux

This is for a black box Linux machine (say a little Raspberry Pi 3B+ and up), or even a Desktop machine.

## Prepare a dedicated user (recommended)

This is not mandatory but recommended

    sudo adduser paudio
    # add it to convenient groups
    sudo usermod -a -G cdrom,audio,video,plugdev paudio
    # also for serial access stuff (usbrelay, IR, etc)
    sudo usermod -a -G dialout paudio


## Install Linux Packages

Please notice that only `sudo` commands must be executed under a priviligied user (for example `pi`), other commands such python enviroment, non Debian python packages, CamillaDSP compilation, must be executed under the regular `paudio` user.

### Generic tools and control web page software:

    sudo apt install alsa-utils alsa-ucm-conf jackd2 jackmeter xdotool cdtool \
                     zita-njbridge jacktrip \
                     libportaudio2 libffi-dev git nodejs npm

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

    sudo apt-get install pkg-config libasound2-dev openssl libssl-dev libjack-jackd2-dev

### Compile

You need to adjust RUSTFLAGS for NEON on armv7 chips like Raspberry Pi, Asus Tinker Board, etc. Target-cpu native will autodetect the CPU profile when native compilation (compiling in the same machine). Ignore the below warning for 'neon', it is a simple Rust information.

```
RUSTFLAGS='-C target-feature=+neon -C target-cpu=native' cargo build --release --features jack-backend
    Updating crates.io index
    ...
    ...
    ...
   Compiling CamillaDSP v4.1.3 (/home/paudio/tmp/camilladsp-4.1.3)
warning: unstable feature specified for `-Ctarget-feature`: `neon`
  |
  = note: this feature is not stably supported; its behavior can change in the future

warning: `CamillaDSP` (lib) generated 1 warning
warning: `CamillaDSP` (bin "camilladsp") generated 1 warning (1 duplicate)
    Finished `release` profile [optimized] target(s) in 11m 55s
```


MORE INFO [here](https://github.com/HEnquist/camilladsp/tree/master?tab=readme-ov-file#building)

## Configure pAudio to use Jack

When using JACK, please see **`doc/config_examples`**

MORE INFO [here](https://github.com/HEnquist/camilladsp/tree/master?tab=readme-ov-file#jack) 

## Install the pAudio application

Go to doc/README.md to continue
