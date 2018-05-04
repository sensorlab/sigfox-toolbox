from sfnr.core import SFNRBaseNode

import numpy as np

import json
import socket
import time
import signal

want_stop = False

def handler(signum, frame):
	global want_stop
	print("Stopping replay. Please wait.")
	want_stop = True

class WSTrafficDump:
	M = 1024

	def __init__(self, path):
		self.data_path = path + ".data.bin"
		self.time_path = path + ".timestamps.bin"

	def iter_by_timestamps(self):
		x = np.memmap(self.data_path, dtype=np.uint8, mode='r')
		assert x.shape[0] % self.M == 0

		N = x.shape[0] // self.M

		x = x.reshape((N, self.M))

		t = np.memmap(self.time_path, dtype=np.float64, mode='r')
		assert t.shape[0] == N

		#print("N = %d" % (N,))

		for i in range(N):
			x0 = np.array(x[i,:], dtype=np.float64)
			x0 = x0 * -1

			yield t[i], x0

class SFNRNode(SFNRBaseNode):

	PORT = 7230

	NAME = 'BS spectrum replay'

	SLUG = 'replay'

	TEMPLATE = 'tcpin'

	DESC = """
<p>This node replays old spectrum data obtained from the Sigfox base station from a file.</p>

<p>Output:</p>

<pre>
{
    'data': [ <i>RSSI in dBm</i>, ... ]
    'timestamp': <i>timestamp</i>
}
</pre>

<p>To run back-end for this node, run the following:</p>

<pre>
sfnr -opath=ws_traffic_20170724 replay
</pre>

<p>Where <i>ws_traffic_20170724</i> is the prefix of binary files produced by
the <i>logserver.py</i> script (e.g. <i>ws_traffic_20170724.data.bin</i> and
<i>ws_traffic_20170724.timestamps.bin</i>)"""

	CATEGORY = "sigfox"

	def run(self, opts):
		print("Running node '%s' connecting to port %d" % (self.SLUG, self.PORT))

		path = opts['path']

		self.run_client(path)

	def run_client(self, path):
		wstraffic = WSTrafficDump(path)

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(("localhost", self.PORT))

		signal.signal(signal.SIGTERM, handler)
		signal.signal(signal.SIGINT, handler)

		global want_stop

		for t, x0 in wstraffic.iter_by_timestamps():

			j = json.dumps({
				'timestamp': t,
				'data': list(x0)
			})

			j += '\n'
			s.sendall(j.encode('ascii'))

			time.sleep(.1)

			if want_stop:
				break
