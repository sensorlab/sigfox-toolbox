import argparse
import sys
from sfnr.nodes.replay import WSTrafficDump
import progressbar
import json

from sfnr.core import SFNRBaseNode
import sfnr.config.sigfox as cfg
import numpy as np
import cv2


class SFNRNode(SFNRBaseNode):

	PORT = 7216

	NAME = 'Burst tagger'

	SLUG = 'btagger'

	DESC = """
<p>Detect transmission bursts on a waterfall diagram. The algorithm works using
a moving window, hence it will take some time before the first bursts are
reported on the output.</p>

<p>Waterfall diagram input:</p>

<pre>
{
    'data': [ <i>RSSI in dBm</i>, ... ]
    'timestamp': <i>timestamp</i>
}
</pre>

<p>Output:</p>

<pre>
{
    'bursts': [
        {
	    'tstart': <i>burst start time</i>,
	    'tstop': <i>burst stop time</i>,
	    'fc': <i>burst central frequency</i>,
	    'bw': <i>burst bandwidth</i>,
	    'bold': <i>whether the burst should be emphasized on display</i>,
	    'text': <i>text to show with the burst</i>,
	    'data': [ <i>RSSI in dBm</i>, ... ]
	},
	...
    ]
}
</pre>

<p>To run back-end for this node, run the following:</p>

<pre>
sfnr btagger
</pre>"""

	CATEGORY = "sigfox"

	def __init__(self):
		# detection window size
		self.N = 300

		# perform detection every Nstep
		self.Nstep = self.N // 10

		self.x = np.empty((self.N, cfg.M))
		self.t = np.empty(self.N)
		self.i = 0

		self.burst_dedup = dict()

	def work(self, msg):
		self.spectrum_update(msg)

		if (self.i >= self.N) and (self.i % self.Nstep == 0):
			bursts = self.detect_bursts_dedup()
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

			if h > self.Nstep:
				print("Saw burst with length %d (> Nstep = %d)" % (h, self.Nstep))

			tstart = self.t[y]
			tstop = self.t[y+h-1]

			f1 = cfg.bin_to_freq(x)
			f2 = cfg.bin_to_freq(x+w)

			data = self.x[y:y+h,x:x+w]

			fc = (f1 + f2)/2
			bw = (f2 - f1)

			ppeak = np.max(self.x[y:y+h-1,x:x+w-1])

			text = "%.6f MHz  %.1f s\n%4.0f dBm  %6.3f kHz" % (
					fc/1e6, tstop-tstart, ppeak, bw/1e3)

			bursts.append({
				'tstart': tstart,
				'tstop': tstop,
				'binfirst': x,
				'binlast': x+w,
				'fc': fc,
				'bw': bw,
				'text': text,
				'bold': int(ppeak > -100),
				'data': data.tolist(),
				})

		#print("detected %d bursts" % (len(bursts),))

		return bursts

	def detect_bursts_dedup(self):

		# Find all bursts in the current window
		bursts = self.detect_bursts()

		def get_key(burst):
			return (burst['tstart'], burst['tstop'], burst['binfirst'], burst['binlast'])

		ret_bursts = []

		for burst in bursts:
			key = get_key(burst)

			# If we have already sent out this burst, ignore.
			if key not in self.burst_dedup:

				# Only sent out bursts that are inside the Nstep margin
				# at the start and stop of the window.
				if burst['tstop'] < self.t[-self.Nstep] \
						and burst['tstart'] > self.t[self.Nstep]:

					ret_bursts.append(burst)
					self.burst_dedup[key] = burst

		# Clean up the deduplication buffer
		for key in list(self.burst_dedup.keys()):

			burst = self.burst_dedup[key]
			if burst['tstop'] < self.t[0]:
				del self.burst_dedup[key]

		return ret_bursts

	def spectrum_update(self, msg):

		self.x[:-1,:] = self.x[1:,:]
		self.x[-1,:] = msg['data']

		self.t[:-1] = self.t[1:]
		self.t[-1] = msg['timestamp']

		self.i += 1


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', required=True,
			help="Path to the wstraffic file to process (without .data.bin suffix)")
	parser.add_argument('-o', '--output', required=True,
			help="Path to write the output JSON file to")

	args = parser.parse_args()

	wstraffic = WSTrafficDump(args.input)

	node = SFNRNode()

	widgets = [ progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA() ]
	maxval = wstraffic.get_timestamps().shape[0]
	pbar = progressbar.ProgressBar(widgets=widgets, maxval=maxval)

	print("N =", maxval)

	i = 0
	pbar.start()

	bursts = []
	for t, x0 in wstraffic.iter_by_timestamps():

		msg = {
			'timestamp': t,
			'data': x0
		}

		rv = node.work(msg)

		for burst in rv['bursts']:
			del burst['data']
			del burst['text']
			del burst['bold']
			bursts.append(burst)

		pbar.update(i)
		i += 1

	pbar.finish()

	with open(args.output, "w") as f:
		json.dump(bursts, f, indent=4)
