# Number of signal samples per record (size of the FFT, determines frequency
# resolution)
Ns = 5000

# Ideal central frequency of the spectrum sensor (hertz)
fc = 868.2e6

# Frequency correction - deviation of the real spectrum sensor central
# frequency from the ideal (hertz).
fc_corr = 91.8e3

# Spectrum sensor sampling rate (hertz)
fs = 1e6

# Minimum and maximum SIGFOX microchannel frequency (inclusive, hertz)
f_min = 868055e3
f_max = 868205e3

# Limited band, for demo
#f_max = 868075e3

# Number of candidate channels selected for transmissions by the selector block.
Nselector = 50
