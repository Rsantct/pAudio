**THIS IS A DRAFT, PENDING TO REVIEW**


# Full Range example

Filters can be set into **`lspk.yml`**, whit a logical syntax, see example file.

Sections in `lspk.yml`:

    safe_gain:      usually negative gain to compensate for loudspeaker filtering,
                    for example a bass extension eq

    lspk_eq:    filters intended to EQ the loudspeaker itself

    drc:        sets of filters per channel for DRC (Digital Room Correction)


Filters can be both IIR or FIR types, with the proper CamillaDSP syntax.

## IIR filtering

Filter data is defined verbosely with CamillaDSP syntax.


## FIR filtering

Filter data is defined verbosely with CamillaDSP syntax. Also the correspondig coefficient PCM files must exist under their corresponding SAMPLERATE folder.

The PCM files provided here are fake ones, just to illustrate `.pcm` files naming

