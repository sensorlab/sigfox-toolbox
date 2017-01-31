from sfnr.core import SFNRBaseNode
import numpy as np

class SFNRNode(SFNRBaseNode):

	PORT = 7212

	NAME = 'FFT'

	SLUG = 'fft'

	DESC = """
<p>Perform a discrete Fourier transform on signal samples and return spectral power density.</p>

<p>Input:</p>

<pre>
{
    'timestamp': <i>timestamp</i>
    'data': [ <i>samples</i> ]
}
</pre>

<p>Output:</p>

<pre>
{
    'timestamp': <i>timestamp</i>
    'fft': [ <i>fft bins</i> ]
}
</pre>

<p>To run back-end for this node, run the following:</p>

<pre>
sfnr fft
</pre>"""

	CATEGORY = "sensing"

	def work(self, msg):
		x = np.array(msg['data'])

		xw = np.hanning(x.shape[0])

		w = np.fft.rfft(x*xw)
		w = w[::-1]

		p = np.real(w*np.conjugate(w))

		nsamples = len(x)
		pn = p / (nsamples**2.) / (2 ** 22)
		pn = np.clip(pn, 1e-15, 1)

		return {
			'timestamp': msg['timestamp'],
			'fft': pn.tolist()
		}
