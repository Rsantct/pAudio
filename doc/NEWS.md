# NEWS

## 2023-dec: CamillaDSP v2.0

- `Volume` filter definition disappears inside `camilladsp.yml`, therefore also from the pipeline `names` section.
- CoreAudio USB external DAC now uses `S32LE`, previously `FLOAT32` was used (maybe a Sonoma issue)

## 2024-jul: MacOS Coreaudio and Linux JACK

- JACK sound server has been implemented for Linux systems, it allows for preamp "input" selector features and more, for instance multiroom JACK to JACK systems.
