# Integration with the PipeWire desktop sound server

https://docs.pipewire.org/index.html

https://pipewire.pages.freedesktop.org/wireplumber/index.html


Modern desktops uses **PipeWire**, for example Ubuntu >= 22.10.

Pipewire does _EMULATE_ a **PulseAudio** like API, in order to player applications like **Spotify** to reach the PipeWire desktop sound server.

PipeWire runs as a user session service. **Wireplumber** is the **PipeWire session manager**. `pipewire-media-session` is deprecated

PipeWire integrates a _JACK EMULATION_, BUT we will NOT use that feature. We want **pAudio** to be compatible with headless systems without PipeWire, through by **our own native JAC**K sound server.

We will configure PipeWire in order to auto magically emerge a couple of jack ports named `PipeWire`, here we will have all the desktop audio streams, like Spotify.

In addition, you should know that PipeWire will automagically release any sound card when used from any application as jackd, zita-alsa-bridge, etc.


## Pipewire configuration

Install the JACK bridge: **`sudo apt install pipewire-jack`**

Prepare the below user session PipeWire / Wireplumber setting files. These files overrides the same general settings of the base configuration `/usr/share/pipewire/pipewire.conf`

These files configures the Pipewire user session behavior so that:

- Prevent Pipewire to use any sound card
- Make Pipewire jack_sink as default, so any desktop App via Pulseaudio/Pipewire will appear under our JACK ports PipeWire_L/R
- Configure a desired resampling quality for any desktop App that plays using Pulseaudio/Pipewire (you can fine tune it by editing `paudio-client.conf`)

You'll find a copy of these files under the **`pAudio/code/share/Linux/.config/`** directory in this repository.



        .config/wireplumber/
        └── main.lua.d
            │
            │   1) Disables the use of any ALSA sound cards in the user session
            │       
            └── 50-disable-all-alsa.lua


        ~/.config/pipewire/
        │
        │
        ├── pipewire.conf.d
        │   │
        │   │   2) Prepares the PipeWire <--> JACK bridge
        │   │       
        │   ├── 10-paudio-jack.conf
        │   │
        │   │   3) Sets the default sink, for BOTH, PipeWire native clients
        │   │      and Pulseaudio clients
        │   │
        │   └── 50-paudio-default-sink.conf
        │
        ├── client.conf.d
        │   │
        │   │   4) Resampling settings for PipeWire native clients
        │   │
        │   └── paudio-client.conf
        │
        │
        └── pipewire-pulse.conf.d
            │
            │   5) Resampling settings for PulseAudio clients
            │
            └── paudio-pipewire-pulse.conf


You can check the wanted setting:

        $ wpctl status
        PipeWire 'pipewire-0' [1.0.5, rafax@salon64, cookie:1040499081]
         └─ Clients:
                34. xdg-desktop-portal                  [1.0.5, rafax@salon64, pid:2524]
                35. pipewire                            [1.0.5, rafax@salon64, pid:4618]
                36. WirePlumber                         [1.0.5, rafax@salon64, pid:4621]
                37. WirePlumber [export]                [1.0.5, rafax@salon64, pid:4621]
                52. gnome-shell                         [1.0.5, rafax@salon64, pid:1849]
                53. GNOME Volume Control Media Keys     [1.0.5, rafax@salon64, pid:2016]
                54. GNOME Shell Volume Control          [1.0.5, rafax@salon64, pid:1849]
                55. spotify                             [1.0.5, rafax@salon64, pid:4741]
                61. wpctl                               [1.0.5, rafax@salon64, pid:40079]

        Audio
         ├─ Devices:
         │                NO DEVICES SHOULD BE LISTED HERE
         │
         ├─ Sinks:
         │  *   38. JACK Sink                           [vol: 1.00]
         │
         ...
         ...


**Recommended:** monitor the CPU load and posible errors/xruns by running:
- `qjackctl`
- `pw-top`




## OLD Pulseaudio configurations

If you came from a `pe.audio.sys/config/config.yml` based in PulseAudio, **YOU SHOULD NOT USE** the plugin **`pulseaudio-jack-sink.py`** anymore.

## Desktop player App users

After restarting **pAudio**, you'll need to restart any desktop player App in order to reconnect to the new PipeWire-Jack instance. See the attached doc about that.
    
