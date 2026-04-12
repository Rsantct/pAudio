# NEWS

## 2023-dec: CamillaDSP v2.0

- `Volume` filter definition disappears inside `camilladsp.yml`, therefore also from the pipeline `names` section.
- CoreAudio USB external DAC now uses `S32LE`, previously `FLOAT32` was used (maybe a Sonoma issue)

## 2024-jun: MacOS Coreaudio and Linux JACK

- JACK sound server has been implemented for Linux systems, it allows for preamp "input" selector features and more, for instance multiroom JACK to JACK systems.

## 2025-dec: players management

- new code for players management: librespot (Spotify Connect client)
- minor fixes

## 2026-jan CamillaDSP v3
- pycamilladsp volume commands changes

## 2026-apr CamillaDSP v4
- new format variants descriptors for devices an raw FIR filter encoding
