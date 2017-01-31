from sfnr.core import SFNRBaseNode
from sfnr.config.sensing import Ns, fc, fs

import json
import socket
import time

from vesna.spectrumsensor import SpectrumSensor, SweepConfig

class SFNRNode(SFNRBaseNode):

	PORT = 7220

	NAME = 'SNE-ESHTER sensor'

	SLUG = 'sensor'

	TEMPLATE = 'tcpin'

	DESC = """
<p>Get data from a SNE-ESHTER spectrum sensor. Note: this node returns a JSON string, not an object, so you need to pass its output through a <i>json</i> node first!</p>

<p>Output:</p>

<pre>
{
    'timestamp': <i>timestamp</i>
    'data': [ <i>samples</i> ]
}
</pre>

<p>To run back-end for this node, run the following:</p>

<pre>
sfnr -osensor_url=socket://<i>ip</i>:2101 sensor
</pre>"""

	CATEGORY = "sensing"

	def run(self, opts):
		print("Running node '%s' connecting to port %d" % (self.SLUG, self.PORT))

		# e.g. "socket://193.2.205.196:2101"
		sensor_url = opts['sensor_url']

		self.run_client(sensor_url)

	def run_client(self, sensor_url):
		sensor = SpectrumSensor(sensor_url)

		config_list = sensor.get_config_list()

		# note: there is currently no programmatic way of
		# getting device config from sampling rate "fs".
		device_config = config_list.get_config(0, 3)

		sample_config = device_config.get_sample_config(fc, Ns)

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(("localhost", self.PORT))

		def callback(sample_config, data):

			j = json.dumps({
				'local_timestamp': time.time(),
				'timestamp': data.timestamp,
				'data': data.data
			})

			j += '\n'
			s.sendall(j.encode('ascii'))

			return True

		sensor.sample_run(sample_config, callback)
