# `librespot`

https://github.com/librespot-org/librespot

## Compile

Regular compiling works well in Raspberry Pi 3B+ with 32 bit OS, but with 64 bits OS things seems to grow up too much, if so go to below to **cross-compiling**

### Install Rust

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

### Install dependencies

    sudo apt install build-essential libasound2-dev libavahi-compat-libdnssd-dev pkg-config libjack-jackd2-dev libpulse0 libpulse-dev

### Compile

    cargo build --no-default-features --features "alsa-backend jackaudio-backend pulseaudio-backend with-dns-sd" librespot

The binary will be usually dropped under your cargo folder at ~/.cargo/bin/


## Cross-compiling

https://github.com/librespot-org/librespot/wiki/Cross-compiling

Following steps works well in a MacBook Pro  M1

### Install Docker

Docker Desktop in Mac or Linux with desktop, or docker package in a headless sever.

### Install Rust

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

### Clone librespot from GitHub

    cd ~/Downloads
    git clone https://github.com/librespot-org/librespot.git
    cd librespot
    git checkout v0.8.0

### Prepare the cross-compiler Dockerfile

For JACK usage, modify the RUN ... section in the provided `contrib/Dockerfile` so that it has the needed libraries:

    RUN dpkg --add-architecture arm64 && \
        dpkg --add-architecture armhf && \
        dpkg --add-architecture armel && \
        apt-get update && \
        apt-get install -y \
        build-essential \
        cmake \
        crossbuild-essential-arm64 \
        crossbuild-essential-armel \
        crossbuild-essential-armhf \
        curl \
        git \
        libasound2-dev \
        libasound2-dev:arm64 \
        libasound2-dev:armel \
        libasound2-dev:armhf \
        libclang-dev \
        libpulse0 \
        libpulse0:arm64 \
        libpulse0:armel \
        libpulse0:armhf \
        libpulse-dev \
        libpulse-dev:arm64 \
        libpulse-dev:armel \
        libpulse-dev:armhf \
        libjack-jackd2-dev \
        libjack-jackd2-dev:arm64 \
        libjack-jackd2-dev:armel \
        libjack-jackd2-dev:armhf \
        libavahi-compat-libdnssd-dev \
        libavahi-compat-libdnssd-dev:arm64 \
        libavahi-compat-libdnssd-dev:armel \
        libavahi-compat-libdnssd-dev:armhf \
        libssl-dev \
        libssl-dev:arm64 \
        libssl-dev:armel \
        libssl-dev:armhf \
        pkg-config \
        rustup

### Build the the Docker cross-compiler image:

    docker build -t librespot-cross -f contrib/Dockerfile .

### For single architecture, run the docker like this:

For example, for Raspberry Pi 64 bits OS we need **aarch64**

    docker run -v /tmp/librespot-build:/build librespot-cross cargo build --release --target aarch64-unknown-linux-gnu --no-default-features --features "alsa-backend jackaudio-backend pulseaudio-backend with-dns-sd native-tls"

### Find the binary

For intel x_86_x64:
    
    /tmp/librespot-build/release/librespot

For aarch64:

    /tmp/librespot-build/aarch64-unknown-linux-gnu/release/librespot

## Copy the binary to the Raspberry Pi device

Use sftp or similar.


## Cleaning

    cd
    rm -rf /tmp/librespot-build
    rm -rf ~/Downloads/librespot 


