
## pAudio `config.yml`

The **`pAudio/config.yml`** main file is about sound devices, sources and an general settigns.

### Dither

To a apply dither at the very end of the processing signal path, it depends on whether you use:
- Coreaudio (macOS), dither will applied by CamillaDSP. Set `dither: true` under the `coreaudio/devices/playback` section
- Jack (Linux), dither will be applied by the jack sound card backend. Set `dither: true` under the `jack` section.

### Jack backend and its CPAL layer

The CPAL-JACK backend produces CamillaDSP xrun cpal errors when the intermediate cpal layer does not detect camilladsp packets.

    JackEngine::XRun: client = cpal_client_in was not finished, state = Running
    JackAudioDriver::ProcessGraphAsyncMaster: Process error
    ...
    ...

The most stable option is to configure CamillaDSP so that it never pauses automatically.:

    - config.yml - 

    expert_zone:
        disable_silence_timeout: true
    
**Notice** that CPU load will not decrease anymore, so you may consider to include a `paudio_restart.sh stop` entry in your daily crontab.

## Loudspeaker configuration `lspk.yml`

The loudspeaker configuration is defined in **`pAudio/loudspeakers/myLoudspeaker/lspk.yml`** (see pAudio/loudspeakers/examples for further info)
