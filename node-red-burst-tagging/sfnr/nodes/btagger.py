from sfnr.core import SFNRBaseNode
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
		self.M = 1024
		self.N = 150

		self.x = np.empty((self.N, self.M))
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

		thresh = cv2.threshold(self.x, -121, 255, cv2.THRESH_BINARY)[1]

		def dilate(x):
			n = 100

			x0 = np.zeros((x.shape[0]+n*2, x.shape[1]+n*2))
			x0[n:-n,n:-n] = x

			kernel = np.array([[1, 1, 1]])

			x0 = cv2.dilate(x0, None, iterations=1)
			x0 = cv2.dilate(x0, kernel, iterations=n)
			x0 = cv2.erode(x0, kernel, iterations=n)

			return x0[n:-n,n:-n]

		thresh = dilate(thresh)
		thresh = np.array(thresh, dtype=np.uint8)

		cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]

		bursts = []

		for c in cnts:
			if cv2.contourArea(c) < 10:
				continue

			(x, y, w, h) = cv2.boundingRect(c)

			tstart = self.t[y]
			tstop = self.t[y+h-1]
			fc = (x+w/2.)/2.
			bw = w/2.

			ppeak = np.max(self.x[y:y+h-1,x:x+w-1])

			text = "fc=%.0f Hz BW=%.0f Hz\nt=%.1f s Ppeak=%.0f dBm" % (
					fc, bw, tstop-tstart, ppeak)

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
