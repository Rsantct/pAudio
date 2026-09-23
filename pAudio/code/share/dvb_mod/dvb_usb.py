#!/usr/bin/env python3

import subprocess
import sys
from   pathlib import Path


def read(path):
    try:
        return path.read_text().strip()
    except (OSError, IOError):
        return ""


def get_lsusb_name(vid, pid):
    """
    Usa lsusb para obtener la descripción del dispositivo USB.
    Ejemplo:
        187f:0201 -> Siano Mobile Silicon Nova B
    """
    result = subprocess.run(
        ["lsusb", "-d", f"{vid}:{pid}"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0 or not result.stdout.strip():
        return ""

    # lsusb:
    # Bus 004 Device 003: ID 187f:0201 Siano Mobile Silicon Nova B
    line = result.stdout.strip()

    marker = f"ID {vid}:{pid}"

    if marker in line:
        return line.split(marker, 1)[1].strip()

    return line


def find_usb_parent(path):
    """
    Sube por el árbol sysfs hasta encontrar el dispositivo USB
    que contiene idVendor e idProduct.
    """
    for parent in [path, *path.parents]:
        vid = read(parent / "idVendor")
        pid = read(parent / "idProduct")

        if vid and pid:
            return parent, vid, pid

    return None, None, None


def find_by_name(name):
    """
    Busca el frontend DVB cuyo dispositivo USB, según lsusb,
    contiene el nombre solicitado.
    """
    name = name.lower()

    for frontend in Path("/sys/class/dvb").glob("dvb*.frontend0"):

        real_path = frontend.resolve()

        usb, vid, pid = find_usb_parent(real_path)

        if usb is None:
            continue

        description = get_lsusb_name(vid, pid)

        if name not in description.lower():
            continue

        # dvb0.frontend0 -> adapter0
        dvb_name = frontend.name
        adapter = int(dvb_name.split(".")[0][3:])

        return adapter, description

    return None, None
