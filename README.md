# pAudio v0.1

A PC based advanced preamplifier, with FIR based EQ and active loudspeaker XOVER management.

This is a system-wide audio control for a MacOS (or Linux PC), so that you can EQ and control all the audio sent to your DAC, Audio Interface, or Headphones.

External sources (vinyl and other analog stuff) can be processed With a high quality inputs sound card.

Some features:

- Calibrated volume listening level supported by an **EBU R128 Loudness monitor** to check the loudness of any recording.

- Advanced Hi-Fi like _loudness_ control, with ISO 226:2003 standard equal **loudness compensation curves for low SPL listening** without loosing low and high bands perception.

- Hi-Fi like preamp controls: volume, tone, balance, subsonic, stereo/mono/midside/polarity, mute, loudness

- **Target curves** and **DRC (digital room correction)**

- Active loudspeaker **FIR based EQ and XOVER** (Full Range or Multiway)

- Easy **control from any web browser** (phone, tablet, PC, ...)

<img src="doc/img/pAudio%20web%20-20dB.png" width="350"><img src="doc/img/pAudio%20web%200dB.png" width="350">


# Credits

pAudio is based on [CamillaDSP](https://github.com/HEnquist/camilladsp#readme) a very powerful audio processing tool, for **Mac** and **Linux**.

Loudness compensation curves follow ISO 226:2003, from my other project [audiotools](https://github.com/Rsantct/audiotools/tree/master/convolver_eq). Here these freq domain curves are converted to FIR to be used in CamillaDSP convolution filtering.

I have also worked on [pe.audio.sys](https://github.com/Rsantct/pe.audio.sys), a similar **Linux** project based on [Brutefir](https://torger.se/anders/brutefir.html), the most powerful convolution engine for Linux.

pAudio and pe.audio.sys are inspired on the [pre.di.c](https://github.com/rripio/pre.di.c) and the former [FIRtro](https://github.com/AudioHumLab/FIRtro) projects, PC based digital preamplifier and crossover projects, designed by the pioneer **@rripio** and later alongside others contributors.

