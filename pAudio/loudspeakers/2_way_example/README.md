## 2 way example

All pcm files here are fake ones, just to illustrate `.pcm` files naming


XOVER
- **gain**
- **delay**
- **polarity**

are set in _human readable_ format in the **`outputs:`** section inside the `lspk.yml` file.

XOVER can use both types of filters: FIR and/or IIR, see the **`lskp.yml`** SAMPLE file.

XOVER set filters can have `flat_gain` and/or `posit_gain` parameters if needed to ensure balanced gains across all filter sets.

`posit_gain` is mean to calculate the gain chain headroom.

The `gain` column in `outputs:` is mainly to compensate for the amplifier and driver efficiency chain.
