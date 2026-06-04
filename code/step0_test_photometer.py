## This is using the PR670 class I wrote based on psychopy but does not require psychopy on the path per se
import time
import matplotlib.pyplot as plt
from PR670_LT import PR670

port = "COM7"
pr = PR670(port)

pr.startRemoteMode()

# # LUMINANCE
print("***Measuring Luminance***")
start_time = time.time()
lum, x, y = pr.measure_luminance_xy()
print(f"luminance {lum}")
elapsed = time.time() - start_time
print(f"Elapsed time for luminance measure: {elapsed:.3f} seconds")

# SPECTRUM
print("***Measuring Spectrum***")
start_time = time.time()
nm, power = pr.measure_spectrum()
print(nm, power)
elapsed = time.time() - start_time
print(f"Elapsed time for spectrum measure: {elapsed:.3f} seconds")
plt.plot(nm, power, "g")
plt.xlabel("wavelength")
plt.ylabel("power")
plt.show(block=True)

pr.endRemoteMode()
