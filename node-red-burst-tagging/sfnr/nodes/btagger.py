from sfnr.core import SFNRBaseNode
import sfnr.config.sigfox as cfg
import numpy as np
import cv2


class SFNRNode(SFNRBaseNode):

	PORT = 7216

	NAME = 'Burst tagger'

	SLUG = 'btagger'

	DESC = """
<p>Perform a discrete Fourier transform on signal samples and return the power spectrum.</p>

<p>Input:</p>

<pre>
{
    ...
    'data': [ <i>samples</i> ]
}
</pre>

<p>Output:</p>

<pre>
{
    ...
    'fft': [ <i>fft bins</i> ]
}
</pre>

<p>To run back-end for this node, run the following:</p>

<pre>
sfnr fft
</pre>"""

	CATEGORY = "sigfox"

	def run(self, opts):
		self.N = 150

		self.x = np.empty((self.N, cfg.M))
		self.t = np.empty(self.N)
		self.i = 0

		super().run(opts)

	def work(self, msg):
		if self.i < self.N:
			self.spectrum_update(msg)

		if self.i >= self.N:
			bursts = self.detect_bursts()
			self.i = 0
		else:
			bursts = []

		return {'bursts': bursts}

	def detect_bursts(self):

		xc = cv2.GaussianBlur(self.x, (5,5), 0)
		xc = np.array(xc, dtype=np.uint8)

		thresh = cv2.adaptiveThreshold(xc, 1,
				cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
				cv2.THRESH_BINARY, 101, -1)

		def dilate(x):
			n = 100

			x0 = np.zeros((x.shape[0]+n*2, x.shape[1]+n*2), dtype=np.uint8)
			x0[n:-n,n:-n] = x

			kernel = np.array([[1, 1, 1]])

			x0 = cv2.erode(x0, None, iterations=1)
			x0 = cv2.dilate(x0, None, iterations=2)
			x0 = cv2.dilate(x0, kernel, iterations=n)
			x0 = cv2.erode(x0, kernel, iterations=n)

			return x0[n:-n,n:-n]

		thresh = dilate(thresh)

		cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]

		bursts = []

		for c in cnts:
			(x, y, w, h) = cv2.boundingRect(c)

			if h*w < 30:
			        continue

			tstart = self.t[y]
			tstop = self.t[y+h-1]

			f1 = cfg.bin_to_freq(x)
			f2 = cfg.bin_to_freq(x+w)

			fc = (f1 + f2)/2
			bw = (f2 - f1)

			ppeak = np.max(self.x[y:y+h-1,x:x+w-1])

			text = "%.6f MHz %.1f s\n%.0f dBm %.3f kHz" % (
					fc/1e6, tstop-tstart, ppeak, bw/1e3)

			bursts.append({
				'tstart': tstart,
				'tstop': tstop,
				'fc': fc,
				'bw': bw,
				'text': text,
				})

		print("detected %d bursts" % (len(bursts),))

		return bursts

	def spectrum_update(self, msg):
		self.x[self.i,:] = msg['data']
		self.t[self.i] = msg['timestamp']

		self.i += 1
