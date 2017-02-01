from sfnr.core import SFNRBaseNode
from sfnr.config.sensing import Ns, fc, fc_corr, fs, f_min, f_max
import numpy as np

class SFNRNode(SFNRBaseNode):

	PORT = 7214

	NAME = 'PSD selector'

	SLUG = 'psdselector'

	DESC = """
<p>Choose a set of central frequencies for transmissions. Frequencies with minimal measured power spectral density are selected.</p>

<p>Input:</p>

<pre>
{
    ...
    'psd': [ <i>fft bins</i> ]
}
</pre>

<p>Output:</p>

<pre>
{
    ...
    'f_tx': [ <i>frequency in hertz</i> ]
}
</pre>

<p>To run back-end for this node, run the following:</p>

<pre>
sfnr psdselector
</pre>"""

	CATEGORY = "sensing"

	def work(self, msg):
		psd = np.array(msg['psd'])

		N = 50

		# spectrum sensor's fc (corrected)
		fc_real = fc - fc_corr

		# list of candidate frequencies
		f_tx = []

		# choose N most vacant frequencies
		for i in np.argsort(psd):

			# ignore DC component
			if i == 0:
				continue

			f = fc_real - fs/4. + fs * float(i)/Ns

			if f < f_min or f > f_max:
				continue

			f_tx.append(f)

			# because resolution of sensor is 200 Hz and
			# we have microchannels at 100 Hz raster
			f_tx.append(f + 100.)

			if len(f_tx) >= N:
				break

		msg['f_tx'] = f_tx

		return msg
