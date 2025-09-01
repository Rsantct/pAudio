#!/usr/bin/env python3
"""
    Based on "The Audio Equalizer Cookbook" by Robert Bristow-Johnson.
"""

import numpy as np

def peaking_biquad_coefficients(freq, gain_db, q, fs):
    """
    Calculate the biquad coefficients for a Peaking EQ filter.

    Args:
        freq (float):       center freq in Hz
        gain_db (float):    gain in dB
        q (float):          Q factor
        fs (int):           samplerate in Hz

    Returns:
        coeficientes biquad (tuple of tuples)
        (b0, b1, b2),  (a0, a1, a2)
    """

    # dB --> lineal (for peaking)
    A = 10**(gain_db / 40.0)
    omega = 2 * np.pi * freq / fs
    alpha = np.sin(omega) / (2 * q)
    cos_omega = np.cos(omega)

    b0 = 1 + alpha * A
    b1 = -2 * cos_omega
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * cos_omega
    a2 = 1 - alpha / A

    # Normalize by a0
    b0_norm = b0 / a0
    b1_norm = b1 / a0
    b2_norm = b2 / a0
    a1_norm = a1 / a0
    a2_norm = a2 / a0

    return (b0_norm, b1_norm, b2_norm), (1.0, a1_norm, a2_norm)


def linkwitz_transform_coefficients(f_act, q_act, f_target, q_target, fs):

    return linkwitz_transform_coefficients_gem_v1(f_act, q_act, f_target, q_target, fs)


def linkwitz_transform_coefficients_gem_v1(f_act, q_act, f_target, q_target, fs, DCzerodB=False):
    """
    Calcula los coeficientes para un filtro Linkwitz Transform.

    Args:
        f_act (float): Frecuencia -3 dB actual (Hz).
        q_act (float): Qtot actual.
        f_target (float): Frecuencia -3 dB deseada (Hz).
        q_target (float): Qtot deseado.
        fs (float): Frecuencia de muestreo (Hz).

    Returns:
        tuple: Una tupla de NumPy arrays (b, a) que contienen los coeficientes
               del numerador (b) y del denominador (a) del filtro biquad.
               b = [b0, b1, b2]
               a = [a0, a1, a2] (donde a0 siempre es 1 para un filtro normalizado)
    """

    # Frecuencias angulares normalizadas
    w_act = 2 * np.pi * f_act / fs
    w_target = 2 * np.pi * f_target / fs

    # Términos intermedios para la parte de "cancelación" (actual)
    cos_w_act = np.cos(w_act)
    sin_w_act = np.sin(w_act)
    alpha_act = sin_w_act / (2 * q_act)

    # Términos intermedios para la parte de "creación" (deseada)
    cos_w_target = np.cos(w_target)
    sin_w_target = np.sin(w_target)
    alpha_target = sin_w_target / (2 * q_target)

    # Denominador común para los coeficientes (coeficiente 'a0' para la nueva respuesta)
    # Esta es una de las formas de derivar los coeficientes.
    # Se basa en la transformación bilineal de las ecuaciones analógicas.
    # El Linkwitz Transform esencialmente invierte la respuesta actual
    # y aplica la deseada.

    # Coeficientes para la parte de "cancelación" (función inversa de la original)
    # Estos corresponden a los 'b' coeficientes del filtro resultante
    b0_temp = 1 + alpha_act + cos_w_act
    b1_temp = -2 * cos_w_act
    b2_temp = 1 - alpha_act + cos_w_act

    # Coeficientes para la parte de "creación" (función deseada)
    # Estos corresponden a los 'a' coeficientes del filtro resultante
    a0_temp = 1 + alpha_target + cos_w_target
    a1_temp = -2 * cos_w_target
    a2_temp = 1 - alpha_target + cos_w_target

    # Normalización y combinación para el Linkwitz Transform
    # El factor de escala entre los dos filtros
    scale_factor = (f_target / f_act)**2 * (1 / (q_target**2) + (1 / q_act**2) * (f_target / f_act)**2) / (1 / (q_act**2) + 1)


    # La implementación del Linkwitz Transform a menudo se presenta como
    # H(s) = ( (s/w_target)^2 + (s/w_target)/q_target + 1 ) / ( (s/w_act)^2 + (s/w_act)/q_act + 1 )
    # Y luego se convierte a digital usando la transformación bilineal.
    # Vamos a usar la forma más común de las ecuaciones de los coeficientes de un biquad para LT.

    # Usando las fórmulas de Linkwitz (una derivación común para los coeficientes biquad)
    # Estas fórmulas asumen que la frecuencia de muestreo es lo suficientemente alta
    # y que estamos trabajando con un biquad de segundo orden.

    # La implementación estándar del Linkwitz Transform a menudo se ve así:
    # Coeficientes del numerador (se "deshace" la respuesta actual)
    b0_num_raw = (2 * np.pi * f_act / fs)**2 + (2 * np.pi * f_act / fs) / q_act + 1
    b1_num_raw = -2 * ( (2 * np.pi * f_act / fs)**2 - 1 )
    b2_num_raw = (2 * np.pi * f_act / fs)**2 - (2 * np.pi * f_act / fs) / q_act + 1

    # Coeficientes del denominador (se "aplica" la respuesta deseada)
    a0_den_raw = (2 * np.pi * f_target / fs)**2 + (2 * np.pi * f_target / fs) / q_target + 1
    a1_den_raw = -2 * ( (2 * np.pi * f_target / fs)**2 - 1 )
    a2_den_raw = (2 * np.pi * f_target / fs)**2 - (2 * np.pi * f_target / fs) / q_target + 1

    # Este enfoque es una simplificación o una forma diferente de presentar las ecuaciones.
    # Una forma más robusta y ampliamente aceptada para la transformación bilineal de un
    # filtro Linkwitz Transform es la siguiente:

    C = 1.0 / np.tan(np.pi * f_target / fs)
    D = 1.0 / np.tan(np.pi * f_act / fs)

    # Coeficientes para la sección 'numerador' del filtro (que cancela la respuesta actual)
    b_coeffs_raw = np.array([
        (D**2 - D/q_act + 1),
        2 * (1 - D**2),
        (D**2 + D/q_act + 1)
    ])

    # Coeficientes para la sección 'denominador' del filtro (que crea la respuesta deseada)
    a_coeffs_raw = np.array([
        (C**2 - C/q_target + 1),
        2 * (1 - C**2),
        (C**2 + C/q_target + 1)
    ])

    # Se escalan los coeficientes 'b' por la relación de las ganancias en DC para mantener el nivel.
    # Esta es una parte crucial del Linkwitz Transform.
    dc_gain_act = (f_act / q_act)**2 # Ganancia en DC para un sistema de 2º orden Fb y Qb
    dc_gain_target = (f_target / q_target)**2

    # El factor de escala K que se aplica al numerador es la relación de las ganancias en DC
    # de los filtros que se están construyendo.
    K = 1.0
    if DCzerodB:
        K = (f_target / q_target)**2 / (f_act / q_act)**2

    # Normalizar los coeficientes 'a' para que a[0] = 1
    norm_factor_a = a_coeffs_raw[2] # a2_raw
    a = a_coeffs_raw / norm_factor_a

    # Normalizar los coeficientes 'b' y aplicar el factor K
    norm_factor_b = b_coeffs_raw[2] # b2_raw
    b = K * b_coeffs_raw / norm_factor_b

    # OJO para que sea igual que v2 hay que invertir el orden en las tuplas ¿?
    return b[::-1], a[::-1]


def linkwitz_transform_coefficients_gem_v2(f_act, q_act, f_target, q_target, fs, DCzerodB=False):
    """
    Calcula los coeficientes para un filtro Linkwitz Transform.

    Args:
        f_act (float): Frecuencia -3 dB actual (Hz).
        q_act (float): Qtot actual.
        f_target (float): Frecuencia -3 dB deseada (Hz).
        q_target (float): Qtot deseado.
        fs (float): Frecuencia de muestreo (Hz).

    Returns:
        tuple: Una tupla de NumPy arrays (b, a) que contienen los coeficientes
               del numerador (b) y del denominador (a) del filtro biquad.
               b = [b0, b1, b2]
               a = [a0, a1, a2] (donde a0 siempre es 1 para un filtro normalizado)
    """

    # --- Parámetros de la transformación bilineal ---
    # La transformación bilineal convierte un filtro analógico a un filtro digital.
    # C y D son términos intermedios para simplificar las ecuaciones.
    C = 1.0 / np.tan(np.pi * f_target / fs)
    D = 1.0 / np.tan(np.pi * f_act / fs)

    # --- Coeficientes del numerador (b) ---
    # Estos coeficientes "cancelan" la respuesta actual del altavoz.
    # Corresponden a los ceros del filtro Linkwitz Transform.
    # b0_raw, b1_raw, b2_raw son los coeficientes antes de la normalización.
    b0_raw = (D**2 - D / q_act + 1)
    b1_raw = 2 * (1 - D**2)
    b2_raw = (D**2 + D / q_act + 1)

    # --- Coeficientes del denominador (a) ---
    # Estos coeficientes "crean" la respuesta deseada del altavoz.
    # Corresponden a los polos del filtro Linkwitz Transform.
    # a0_raw, a1_raw, a2_raw son los coeficientes antes de la normalización.
    a0_raw = (C**2 - C / q_target + 1)
    a1_raw = 2 * (1 - C**2)
    a2_raw = (C**2 + C / q_target + 1)

    # --- Factor de escala (K) ---
    # El factor de escala asegura que la ganancia en DC (0 Hz) del filtro
    # transformado sea la misma que la del sistema original.
    # Esto es crucial para mantener el nivel de baja frecuencia.
    K = 1.0
    if DCzerodB:
        K = (f_target / q_target)**2 / (f_act / q_act)**2

    # --- Normalización de los coeficientes ---
    # Los coeficientes del denominador 'a' se normalizan dividiendo por a2_raw
    # para que el primer coeficiente (a[0]) sea 1.
    norm_factor_a = a2_raw
    a = np.array([a0_raw, a1_raw, a2_raw]) / norm_factor_a
    # Reordenamos 'a' para que sea [1, a1, a2]
    a = np.array([1.0, a[1], a[0]])


    # Los coeficientes del numerador 'b' se normalizan y se les aplica el factor de escala K.
    # Se dividen por b2_raw (que es el término (D**2 + D/q_act + 1))
    # y luego se multiplican por K.
    norm_factor_b = b2_raw
    b = K * np.array([b0_raw, b1_raw, b2_raw]) / norm_factor_b
    # Reordenamos 'b' para que sea [b0, b1, b2]
    b = np.array([b[2], b[1], b[0]])

    return b, a


def linkwitz_transform_coefficients_gem_v3(f_act, q_act, f_target, q_target, fs, DCzerodB=False):
    """
    Calcula los coeficientes para un filtro Linkwitz Transform.

    Args:
        f_act (float): Frecuencia -3 dB actual (Hz).
        q_act (float): Qtot actual.
        f_target (float): Frecuencia -3 dB deseada (Hz).
        q_target (float): Qtot deseado.
        fs (float): Frecuencia de muestreo (Hz).

    Returns:
        tuple: Una tupla de NumPy arrays (b, a) que contienen los coeficientes
               del numerador (b) y del denominador (a) del filtro biquad.
               b = [b0, b1, b2]
               a = [a0, a1, a2] (donde a0 siempre es 1 para un filtro normalizado)
    """

    # Frecuencias angulares (radianes/segundo) para el dominio analógico.
    # Estas se usan en la derivación de los polinomios analógicos.
    omega_act = 2 * np.pi * f_act
    omega_target = 2 * np.pi * f_target

    # --- Coeficientes del numerador (b) - Derivados de la respuesta ACTUAL ---
    # El numerador del filtro Linkwitz Transform cancela la respuesta existente del altavoz.
    # Se obtiene aplicando la transformación bilineal al polinomio:
    # s^2 + (omega_act/q_act)s + omega_act^2

    # Términos intermedios para el numerador (polinomio actual)
    term_omega_a_sq = omega_act**2 # omega_act^2
    term_omega_a_q_a = omega_act / q_act # omega_act / Q_act
    term_2fs_sq = (2 * fs)**2 # (2 * fs)^2
    term_2fs = 2 * fs # 2 * fs

    # Coeficientes del numerador (b0, b1, b2) antes de la normalización
    # Estos corresponden a los términos de z^0, z^-1, z^-2 respectivamente.
    b0_raw = term_2fs_sq + term_2fs * term_omega_a_q_a + term_omega_a_sq
    b1_raw = -2 * term_2fs_sq + 2 * term_omega_a_sq
    b2_raw = term_2fs_sq - term_2fs * term_omega_a_q_a + term_omega_a_sq

    # --- Coeficientes del denominador (a) - Derivados de la respuesta DESEADA ---
    # El denominador del filtro Linkwitz Transform impone la nueva respuesta deseada.
    # Se obtiene aplicando la transformación bilineal al polinomio:
    # s^2 + (omega_target/q_target)s + omega_target^2

    # Términos intermedios para el denominador (polinomio deseado)
    term_omega_t_sq = omega_target**2 # omega_target^2
    term_omega_t_q_t = omega_target / q_target # omega_target / Q_target

    # Coeficientes del denominador (a0, a1, a2) antes de la normalización
    # Estos corresponden a los términos de z^0, z^-1, z^-2 respectivamente.
    a0_raw = term_2fs_sq + term_2fs * term_omega_t_q_t + term_omega_t_sq
    a1_raw = -2 * term_2fs_sq + 2 * term_omega_t_sq
    a2_raw = term_2fs_sq - term_2fs * term_omega_t_q_t + term_omega_t_sq

    # --- Factor de ganancia DC (K) ---
    # Este factor compensa la diferencia en la ganancia de DC entre los dos polinomios
    # analógicos para asegurar que la ganancia de DC del filtro Linkwitz Transform sea correcta.
    # La ganancia en DC del filtro LT es (f_target / f_act)^2.
    dc_gain_factor = 1.0
    if DCzerodB:
        dc_gain_factor = (f_target / f_act)**2

    # --- Normalización final de los coeficientes ---
    # Normalizamos los coeficientes del denominador 'a' dividiendo por a0_raw
    # para que el primer coeficiente (a[0]) sea 1, que es el formato estándar para filtros IIR.
    norm_factor_den = a0_raw
    a = np.array([1.0, a1_raw / norm_factor_den, a2_raw / norm_factor_den])

    # Normalizamos los coeficientes del numerador 'b' dividiendo también por a0_raw
    # (el mismo factor de normalización del denominador) y aplicando el factor de ganancia DC.
    b = dc_gain_factor * np.array([b0_raw / norm_factor_den, b1_raw / norm_factor_den, b2_raw / norm_factor_den])

    return b, a


