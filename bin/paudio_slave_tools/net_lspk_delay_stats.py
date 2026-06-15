#!/usr/bin/env python3

import re
import statistics
import sys


def calcular_estadisticas(ruta_archivo):
    valores_ms = []

    # Expresión regular para buscar el número justo antes de "ms"
    patron = re.compile(r"(\d+\.\d+)\s+ms")

    try:
        with open(ruta_archivo, "r") as archivo:
            for linea in archivo:
                coincidencia = patron.search(linea)
                if coincidencia:
                    valores_ms.append(float(coincidencia.group(1)))

        if not valores_ms:
            print(
                f"No se encontraron valores válidos de 'ms' en: {ruta_archivo}"
            )
            return

        # 1. Cálculo de estadísticas con precisión original
        total_muestras = len(valores_ms)
        minimo = min(valores_ms)
        maximo = max(valores_ms)
        media = statistics.mean(valores_ms)
        mediana = statistics.median(valores_ms)
        desviacion = (
            statistics.stdev(valores_ms) if total_muestras > 1 else 0.0
        )
        rango = maximo - minimo

        # 2. Moda con valores originales (3 decimales)
        modas_originales = statistics.multimode(valores_ms)
        if len(modas_originales) == total_muestras:
            texto_moda_orig = "No hay (valores únicos)"
        else:
            texto_moda_orig = ", ".join([f"{m:.3f} ms" for m in modas_originales])

        # 3. NUEVO: Moda con valores redondeados a 2 decimales
        valores_redondeados = [round(v, 2) for v in valores_ms]
        modas_redondeadas = statistics.multimode(valores_redondeados)

        if len(modas_redondeadas) == total_muestras:
            texto_moda_redon = "No hay (valores únicos incluso al redondear)"
        else:
            texto_moda_redon = ", ".join(
                [f"{m:.2f} ms" for m in modas_redondeadas]
            )

        # Mostrar resultados por consola
        print("-" * 45)
        print(f" Estadísticas de Retardo para: {ruta_archivo}")
        print("-" * 45)
        print(f"Muestras procesadas   : {total_muestras}")
        print(f"Mínimo                : {minimo:.3f} ms")
        print(f"Máximo                : {maximo:.3f} ms")
        print(f"Rango (Max - Min)     : {rango:.3f} ms")
        print(f"Media (Promedio)      : {media:.3f} ms")
        print(f"Mediana               : {mediana:.3f} ms")
        print(f"Desviación Estándar   : {desviacion:.3f} ms")
        print("-" * 45)
        print(f"Moda (Datos reales)   : {texto_moda_orig}")
        print(f"Moda (Redondeado 2D)  : {texto_moda_redon}")
        print("-" * 45)

    except FileNotFoundError:
        print(f"Error: El archivo '{ruta_archivo}' no existe.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "/tmp/lspk_delay_info.log"
    calcular_estadisticas(ruta)
