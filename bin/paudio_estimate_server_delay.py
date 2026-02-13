#!/usr/bin/env python3
""" We take empirical time delay for the pAudio server
    to be running, in different machines to estimate
    a function to estimate the delay depending on
    the machine CPU benchmark.
"""

import  numpy as np
from    scipy.optimize import curve_fit
import  matplotlib.pyplot as plt


# Empirical data when computing sum( i**2 for i in range(500_000) )
#
#                   compute     bench       time to run
#                   time                    the pAudio server
#                   -----       -----       -----
# RPI 3 B           0.895       0.05        32 s
# RPI 3 B+          0.450       0.11        22 s
# Asus Atinker      0.225       0.22        14 s
# Core i3           0.049       1.0          4 s
# Apple M1          0.032       1.5          2 s


# x:  benchmark refered to a Core i3
# y:  pAudio server start delay in seconds
x_data = np.array([0.05, 0.11, 0.22, 1.0, 1.5])
y_data = np.array([32, 22, 14, 4, 2])

# We define the model: f(x) = a * x^b
# This model is ideal for nonlinear decays
def model(x, a, b):
    return a * np.power(x, b)

# Curve adjustement
(a, b), _ = curve_fit(model, x_data, y_data)

print(f"Estimated equation: f(x) = {a:.2f} * x^{b:.2f}")

# --- Plot ---
x_range = np.linspace(0.05, 1.5, 100)
y_pred = model(x_range, a, b)

plt.scatter(x_data, y_data, color='red', label='Empirical data')
plt.plot(x_range, y_pred, label=f'Adjustment: {a:.2f} * x^{b:.2f}')
plt.xlabel('Benchmark referred to Core i3')
plt.ylabel('pAudio server start delay')
plt.legend()
plt.grid(True)
plt.show()

# RESULT:   Estimated equation: f(x) = 5.14 * x^-0.62
