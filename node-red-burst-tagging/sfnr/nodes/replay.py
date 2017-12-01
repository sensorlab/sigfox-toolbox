from sfnr.core import SFNRBaseNode

import numpy as np

import json
import socket
import time
import signal

want_stop = False

def handler(signum, frame):
	global want_stop
	print("Stopping sensor. Please wait.")
	want_stop = True

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
		M = 1024

		data_path = path + ".data.bin"
		time_path = path + ".timestamps.bin"

		x = np.memmap(data_path, dtype=np.uint8, mode='r')
		assert x.shape[0]%M == 0

		n = x.shape[0]//M

		x = x.reshape((n, M))

		t = np.memmap(time_path, dtype=np.float64, mode='r')
		assert t.shape[0] == n

		print("N = %d" % (n,))

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(("localhost", self.PORT))

		signal.signal(signal.SIGTERM, handler)
		signal.signal(signal.SIGINT, handler)

		global want_stop

		i = 0
		while not want_stop:

			x0 = np.array(x[i,:], dtype=np.float64)
			x0 = x0 * -1

			j = json.dumps({
				'timestamp': t[i],
				'data': list(x0)
			})

			j += '\n'
			s.sendall(j.encode('ascii'))

			i = (i + 1) % n

			time.sleep(.1)
