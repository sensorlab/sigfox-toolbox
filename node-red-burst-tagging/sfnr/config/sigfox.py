import numpy as np

# FFT size
M = 1024

# Central frequency
fc = 868.600e6

# Sampling frequency
fs = 192e3

# FFT refresh frequency
fr = 5

_bin_to_freq = fc + fs * np.arange(M)/(M - 1) - fs/2

def bin_to_freq(n):
	n = np.clip(n, 0, len(_bin_to_freq)-1)
	return _bin_to_freq[n]

def freq_to_bin(f):
	return int(np.round(np.interp(f, bin_to_freq, np.arange(len(bin_to_freq)))))
