
## pAudio `config.yml`

The **`pAudio/config.yml`** main file is about sound devices, sources and an general settigns.

### Dither

To a apply dither at the very end of the processing signal path, you can set `dither: true`.

The system will apply dither depending on whether we use:
- Coreaudio (macOS), dither will applied by CamillaDSP. Set `dither: true` under the `coreaudio/devices/playback` section
- Jack (Linux), dither will be applied by the jack sound card driver. Set `dither: true` under the `jack` section.


## Loudspeaker configuration `lspk.yml`

The loudspeaker configuration is defined in **`pAudio/loudspeakers/myLoudspeaker/lspk.yml`** (see pAudio/loudspeakers/examples for further info)
