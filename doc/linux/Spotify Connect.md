# `librespot`

https://github.com/librespot-org/librespot

## Cross-compiling

Follow this https://github.com/librespot-org/librespot/wiki/Cross-compiling


### Install Docker Desktop in your machine

### Install Rust
    
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

### Clone librespot

    cd ~/Downloads
    git clone https://github.com/librespot-org/librespot.git
    cd librespot
    git checkout v0.8.0

### Prepare the cross-compiler Dockerfile

For JACK usage, modify the RUN ... section in the provided `contrib/Dockerfile` with this:

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

    docker run -v /tmp/librespot-build:/build librespot-cross cargo build --release --target aarch64-unknown-linux-gnu --no-default-features --features "alsa-backend jackaudio-backend pulseaudio-backend with-dns-sd native-tls"



