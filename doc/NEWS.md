# NEWS

## 2023-dec: CamillaDSP v2.0

- `Volume` filter definition disappears inside `camilladsp.yml`, therefore also from the pipeline `names` section.
- CoreAudio USB external DAC now uses `S32LE`, previously `FLOAT32` was used (maybe a Sonoma issue)
