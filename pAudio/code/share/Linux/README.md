## Pipewire

We need to aply Pipewire user configurations in order to:

- Prevent Pipewire to use any sound card
- Make Pipewire jack_sink as default, so any desktop App via Pulseaudio/Pipewire will appear under our JACK ports PipeWire_L/R
- Configure a desired resampling quality for any desktop App that plays using Pulseaudio/Pipewire

This is accomplished by the following files:
    
    .config/pipewire
    ├── client.conf.d
    │   └── paudio-client.conf
    ├── pipewire.conf.d
    │   ├── 10-paudio-jack.conf
    │   └── 50-paudio-default-sink.conf
    └── pipewire-pulse.conf.d
        └── paudio-pipewire-pulse.conf
    
    .config/wireplumber/
    └── main.lua.d
        └── 50-disable-all-alsa.lua
