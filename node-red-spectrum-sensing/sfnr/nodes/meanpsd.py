from sfnr.core import SFNRBaseNode
from sfnr.config.sensing import Ns
import numpy as np

class SFNRNode(SFNRBaseNode):

	PORT = 7213

	NAME = 'Mean PSD'

	SLUG = 'meanpsd'

	DESC = """
<p>Ingest power spectrum samples and return power spectral density, averaged over a time window.</p>

<p>Input:</p>

<pre>
{
    ...
    'fft': [ <i>fft bins</i> ]
}
</pre>

<p>Output:</p>

<pre>
{
    ...
    'meanpsd': [ <i>fft bins</i> ]
}
</pre>

<p>To run back-end for this node, run the following:</p>

<pre>
sfnr meanpsd
</pre>"""

	CATEGORY = "sensing"

	HIST_SIZE = 1000

	def __init__(self):
		super().__init__()

		Ws = Ns//2+1
		self.hist = np.empty((self.HIST_SIZE, Ws))
		self.cnt = 0

	def _ingest(self, w):
		self.hist = np.roll(self.hist, 1, axis=0)
		self.hist[0,:] = w

		self.cnt += 1

	def _get_hist(self):
		hist_fill = min(self.cnt, self.HIST_SIZE)
		return self.hist[:hist_fill,:]

	def _get_psd(self):
		return np.mean(self._get_hist(), axis=0)

	def work(self, msg):

		w = np.array(msg['fft'])
		self._ingest(w)

		msg['meanpsd'] = self._get_psd().tolist()

		return msg
