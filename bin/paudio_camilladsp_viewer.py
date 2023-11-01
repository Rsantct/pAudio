#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez

import  os
from    time import sleep
import  json
from    camilladsp import CamillaConnection

PC = CamillaConnection("127.0.0.1", 1234)


def printa():

    vol = PC.get_volume()
    drc_gain = PC.get_config()["filters"]["drc_gain"]["parameters"]["gain"]
    muted = PC.get_mute()

    ppl = PC.get_config()["pipeline"]
    ppl_L = ppl[1]["names"]
    ppl_R = ppl[2]["names"]

    print('vol:', vol, '(muted)' if muted else '')
    print('drc gain:', drc_gain)
    print(ppl_L)
    print(ppl_R)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":

    clear()

    while True:

        try:
            PC.connect()
            printa()
            PC.disconnect()
        except:
            print('- not connected -')

        sleep(.5)
        clear()
