import numpy as np
from numpy.lib.stride_tricks import as_strided

class ChannelQualityMethod(object):
	"""Calculate channel quality measure based on a history of RSSI
	measurements.

	This is base class from which all other channel quality metric
	derive. All metrics use the same interface:

	cq = method.get_cq(rssi, t)

	rssi[i,j] is RSSI measurement (in dB log scale) at time t[i],
	frequency channel j. i = 0...N-1, j = 0...M-1.

	cq[j] is CQ measure for frequency channel j. j = 0...M-1.

	Any parameters for the method are passed to its constructor:

	method = ChannelAvailabilityMethod(Rthr=-100)
	cq = method.get_cq(rssi)
	"""

	def get_cq(self, rssi, t):
		"""get_cq(rssi, t) -> list

		Calculate channel quality for all channels from a matrix of
		RSSI measurements.
		"""
		M = rssi.shape[1]
		cq = np.empty(shape=M)
		for j in range(M):
			cq[j] = self.get_cq_ch(rssi[:,j], t)

		return cq

	def get_cq_ch(self, rssi_ch, t):
		"""get_ch_ch(rssi_ch, t) -> float

		Calculate channel quality for a single channel.
		"""
		raise NotImplementedError


class ChannelAvailabilityMethod(ChannelQualityMethod):
	"""Channel availability - percentage of time RSSI in a channel is below
	a threshold.

	Does not take into account time distribution of interference.

	Rthr is threshold in dB.
	"""
	def __init__(self, Rthr):
		self.Rthr = Rthr

	def get_cq_ch(self, rssi_ch, t):
		return np.mean(rssi_ch < self.Rthr)


class MeanPSDMethod(ChannelQualityMethod):
	"""Mean power spectral density.

	Does not take into account time distribution of interference.
	"""
	def get_cq_ch(self, rssi_ch, t):
		return np.mean(rssi_ch)


def _find_vacancies(x, thr):
	xpad = np.r_[1, x, 1]

	xt = xpad < thr
	xd = np.diff(np.asarray(xt, dtype=int))

	s0 = np.argwhere(xd)[:,0]+1
	l0 = np.diff(s0)-1

	starts = s0[:-1:2]-1
	lengths = l0[::2]

	return starts, lengths

class CQTauMethod(ChannelQualityMethod):
	"""CQ(tau) method.

	This is a channel quality metric, based on availability of the channel
	over time, which meaningfully quantifies spectrum usage.

	Described in:

	Noda, Claro, et al. "Quantifying the channel quality for
	interference-aware wireless sensor networks."

	Rthr is threshold in dB.

	tmin is minimum vacancy in seconds.

	fs is RSSI sampling frequency in hertz.

	beta is the bias parameter. Higher values of beta mean the method gives
	more weight to longer channel vacancies.
	"""

	def __init__(self, Rthr, tmin, fs, beta):
		self.Rthr = Rthr

		# minimum vacancy length, in samples
		self.lmin = tmin*fs

		self.beta = beta

	def get_cq_ch(self, rssi_ch, t):
		N = rssi_ch.shape[0]

		s, l = _find_vacancies(rssi_ch, self.Rthr)

		a = 0.
		for i in np.argwhere(l >= self.lmin)[:,0]:
			a += l[i]**(1. + self.beta)

		return a/(N - 1)**(1. + self.beta)

class MLEMethod(ChannelQualityMethod):
	"""CQ*(tau) method (MLE)

	This is an adaptation of the CQ(tau) metric that is equivalent to the
	maximum likelyhood estimation of the probability that a packet will not
	be interfered with.

	It assumes that if interference power is above a fixed threshold at any
	time during the transmission of a packet, the packet will be lost.

	Rthr is threshold in dB.

	tlen is length of the packet in seconds.

	fs is RSSI sampling frequency in hertz.
	"""

	def __init__(self, Rthr, tlen, fs):
		self.Rthr = Rthr

		# packet length, in samples
		self.lmin = tlen*fs

	def get_cq_ch(self, rssi_ch, t):
		N = rssi_ch.shape[0]

		s, l = _find_vacancies(rssi_ch, self.Rthr)

		nvacant = 0
		for i in np.argwhere(l >= self.lmin)[:,0]:
			nvacant += l[i] - self.lmin + 1

		return nvacant/(N - self.lmin)

class SINRMethod(ChannelQualityMethod):
	"""SINR method

	This method gives a more accurate estimate of the expected PRR for a
	channel. In essence it is similar to the MLE method, except that it
	takes into account a realistic PRR(SINR) curve for the basestation.

	The PRR(SINR) curve can be calculated theoretically, or measured.

	tlen is length of the packet in seconds.

	fs is RSSI sampling frequency in hertz.

	ps is signal power at base station.

	ref_sinr and ref_prr give the PRR(SINR) curve of the base station.
	ref_prr[n] is the PRR at ref_sinr[n].
	"""

	def __init__(self, tlen, fs, ps, ref_sinr, ref_prr):
		# number of samples, not length, hence +1
		self.lmin = int(np.ceil(tlen*fs)) + 1

		self.ps = ps

		self.ref_sinr = ref_sinr
		self.ref_prr = ref_prr

	def get_cq_ch(self, rssi_ch, t):

		rssi_lin = 10. ** (rssi_ch/10.)

		rssi_lin_stride = as_strided(
					rssi_lin,
					strides=(rssi_lin.strides[0], rssi_lin.strides[0]),
					shape=(rssi_lin.shape[0] - self.lmin + 1, self.lmin))

		pinlin = np.mean(rssi_lin_stride, axis=1)
		pin = 10. * np.log10(pinlin)

		sinr = self.ps - pin

		prr = np.mean(np.interp(sinr, self.ref_sinr, self.ref_prr))

		return prr
