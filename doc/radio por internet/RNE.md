En un navegador abrimos la página de la Radio Nacional y escuchamos Radio Clásica.

Mirando la consola [Red] veremos las URL m3u8, ejemplo

Directo Estricto / Live
Lista unos pocos fragmentos (habitualmente entre 4 y 6 chunks, 20 a 30 segundos de emisión
    https://rtvelivestream.rtve.es/rtvesec/rne/rne_r2_main.m3u8

Directo con Retorno / DVR - Digital Video Recorder
Lista fragmentos históricos que pueden abarcar varias horas de emisión
    https://rtvelivestream.rtve.es/rtvesec/rne/rne_r2_main_dvr.m3u8



Ejemplo de Master Playlist:

#EXTM3U
#EXT-X-VERSION:3
#EXT-X-INDEPENDENT-SEGMENTS
#EXT-X-STREAM-INF:BANDWIDTH=163000,CODECS="mp4a.40.2",CHANNELS="2"
rne_r2_main-audio_157000=163000.m3u8

Pero RTVE (a través de la plataforma Golumi) está entregando directamente la Media Playlist final en lugar de una Master Playlist adaptativa de múltiples calidades.

Esto es muy común en streams puros de audio (radio), donde al haber solo un flujo o perfil de audio disponible (una única calidad), el servidor omite el paso intermedio de la selección de perfil (#EXT-X-STREAM-INF) y sirve directamente el listado de chunks con su duración (#EXT-X-TARGETDURATION:5).

Veamos la media playlist:

$ curl -s "https://rtvelivestream.rtve.es/rtvesec/rne/rne_r2_main.m3u8"
#EXTM3U
## Created with Golumi Video Platform

#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:5
#EXT-X-MEDIA-SEQUENCE:50510
#EXTINF:4.992,
https://rtvelivestream.rtve.es/rtvesec/rne/GL0/34_2026_07_05_08_10_07_50510.ts
#EXTINF:4.992,
https://rtvelivestream.rtve.es/rtvesec/rne/GL0/34_2026_07_05_08_10_12_50511.ts
#EXTINF:5.013,
https://rtvelivestream.rtve.es/rtvesec/rne/GL0/34_2026_07_05_08_10_17_50512.ts
#EXTINF:4.992,
https://rtvelivestream.rtve.es/rtvesec/rne/GL0/34_2026_07_05_08_10_22_50513.ts

Para ver el codec

$ curl -s "https://rtvelivestream.rtve.es/rtvesec/rne/GL0/34_2026_07_05_08_10_07_50510.ts" | mediainfo -
General
ID                                       : 1 (0x1)
Format                                   : MPEG-TS
Duration                                 : 4 s 949 ms
Overall bit rate mode                    : Variable
Overall bit rate                         : 216 kb/s

Audio
ID                                       : 256 (0x100)
Menu ID                                  : 1 (0x1)
Format                                   : AAC LC
Format/Info                              : Advanced Audio Codec Low Complexity
Format version                           : Version 4
Muxing mode                              : ADTS
Codec ID                                 : 15-2
Duration                                 : 4 s 842 ms
Bit rate mode                            : Variable
Channel(s)                               : 2 channels
Channel layout                           : L R
Sampling rate                            : 48.0 kHz
Frame rate                               : 46.875 FPS (1024 SPF)
Compression mode                         : Lossy
Language                                 : Spanish

