**THIS IS A DRAFT, PENDING TO REVIEW**


# Full Range example


## IIR filtering

IIR filters can be set into **`camilladsp_lspk.yml`**, whit a logical syntax, see example file.

Sections in `camilladsp_lspk.yml`:

    safe_gain:      usually negative gain to compensate for loudspeaker filtering,
                    for example a bass extension eq

    iir_eq:         CamillaDSP filters

        lspk_eq:    filters intended to EQ the loudspeaker itself

        drc:        sets of filters per channel for DRC (Digital Room Correction)


`fir_eq` is not set here, pAudio will take a look for **`xxxx.pcm`** files and will do the needed config.


## FIR filtering _PENDING_

All pcm files are fake ones, just to illustrate `.pcm` files naming

### Optional: full range EQ

If you want to apply some FIR to fine EQ your full range loudspeaker, yo can prepare and add here a file named `xo.fr.pcm`.

If this file is omitted, no loudspeaker filtering will be applied

