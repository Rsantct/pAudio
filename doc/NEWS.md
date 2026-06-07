# NEWS

## 2023-dec: CamillaDSP v2.0

- `Volume` filter definition disappears inside `camilladsp.yml`, therefore also from the pipeline `names` section.
- CoreAudio USB external DAC now uses `S32LE`, previously `FLOAT32` was used (maybe a Sonoma issue)

## 2024-jun: MacOS Coreaudio and Linux JACK

- JACK sound server has been implemented for Linux systems, it allows for preamp "input" selector features and more, for instance multiroom JACK to JACK systems.

## 2025-dec: players management

- New code for players management: librespot (Spotify Connect client)
- Minor fixes

## 2026-jan: CamillaDSP v3
- pycamilladsp volume commands changes

## 2026-apr: CamillaDSP v4
- New format variants descriptors for devices and raw FIR filter encoding

## 2026-may: 
- Improvements on zita based remote peer sources (pAudio native remote sources).
- New JackTrip based remote sources.
- A new script for macOS users allows sending lossless and low latency desktop audio to pAudio via JackTrip.
- New optional automatic jack source switching on signal detection.
- Fix timeout for the pAudio server to be alive on slow machines.
- Fix libresport reading events for metadata retrieving.
- Add shairplay-sync plugin for Airplay receiving.
- All custom configurations now under the pAudio/config/ folder
