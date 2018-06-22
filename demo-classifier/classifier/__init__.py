from sfnr.core import SFNRBaseNode
import numpy as np
from matplotlib.cm import get_cmap
from PIL import Image
from subprocess import check_call
from tempfile import NamedTemporaryFile

def print_burst(x):
	cmap = get_cmap('magma')

	vmin = -130
	vmax = -100

	v = (x - vmin) / (vmax-vmin)
	v = v.clip(0, 1)

	b = cmap(v)[:,:,:3]
	b = np.asarray(b*255, dtype=np.uint8)

	with NamedTemporaryFile(suffix='.png') as f:
		img = Image.fromarray(b, mode='RGB')
		img = img.resize((b.shape[1]*4, b.shape[0]*4))
		img.save(f.name)

		#check_call("eog %s" % (f.name,), shell=True)
		try:
			check_call("tiv -h 5 %s" % (f.name,), shell=True)
		except:
			pass

class DemoClassifier(SFNRBaseNode):

	PORT = 7240

	NAME = 'Demo interference classifier'

	SLUG = 'classifier'

	DESC = ''

	CATEGORY = "sigfox"

	def work(self, msg):

		bursts2 = []

		for burst in msg['bursts']:
			x = np.asarray(burst['data'])
			print_burst(x)

			print("Burst:")
			print("    Duration: %.0f ms" % ((burst['tstop']-burst['tstart'])*1e3,))
			print("    Bandwidth: %.3f kHz" % (burst['bw']/1e3,))
			print("    Frequency: %.3f MHz" % (burst['fc']/1e6,))
			print("    Data (%d x %d)" % (x.shape[1], x.shape[0]))

			cls = self.classifier(burst)
			print("    *** Classification: %s" % cls)
			print()

			if cls != 'unknown':
				burst['text'] = cls
				burst['bold'] = 1
			else:
				burst['bold'] = 0

			bursts2.append(burst)

		msg['bursts'] = bursts2
		return msg

	def classifier(self, burst):
		bw = burst['bw']
		tlen = burst['tstop'] - burst['tstart']

		if bw > 190e3:
			cls = "IEEE 802.15.4";
		elif (bw > 10e3) and (bw < 13e3) and (tlen < 2):
			cls = "proprietary"
		elif (bw > 15e3) and (bw < 22e3) and (tlen < 1):
			cls = "LoRa"
		elif (bw < 2e3) and (tlen > 1):
			cls = "SIGFOX"
		else:
			cls = "unknown"

		return cls

def main():
	opts = {}

	node = DemoClassifier()
	node.run(opts)

if __name__ == "__main__":
	main()
