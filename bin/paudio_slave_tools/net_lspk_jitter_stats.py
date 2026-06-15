#!/usr/bin/env python3

import sys
import numpy as np
from scipy import stats

def calcular_jitter(archivo_log):

    latencias = []

    with open(archivo_log, 'r') as f:

        for linea in f:
            try:
                if "ms" in linea:
                    valor = float(linea.split()[-2])
                    latencias.append(valor)
            except (ValueError, IndexError):
                continue

    if not latencias:
        print("No se encontraron métricas válidas.")
        return

    # Convertir a NumPy array
    datos = np.array(latencias)

    # El jitter se define formalmente como la media de las diferencias absolutas consecutivas
    diferencias = np.abs(np.diff(datos))
    jitter_medio = np.mean(diferencias)

    print("--- Análisis de Jitter y Latencia ---")
    print(f"Muestras analizadas: {len(datos)}")
    print(f"Latencia Media:      {np.mean(datos):.3f} ms")
    print(f"Latencia Mediana:    {np.median(datos):.3f} ms")
    print(f"Moda:                {stats.mode(datos, keepdims=True).mode[0]:.3f} ms")
    print(f"Desviación Estándar: {np.std(datos):.3f} ms")
    print(f"Jitter Medio (RFC):  {jitter_medio:.3f} ms")
    print(f"Jitter Máximo:       {np.max(diferencias):.3f} ms")


if __name__ == "__main__":

    archivo_log = '/tmp/lspk_delay_info.log'

    if sys.argv[1:]:
        archivo_log = sys.argv[1]

    calcular_jitter(archivo_log)
