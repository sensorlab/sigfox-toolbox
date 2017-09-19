from sfnr.core import SFNRBaseNode
import numpy as np
import pygame
from matplotlib.cm import get_cmap


class SFNRNode(SFNRBaseNode):

	PORT = 7215

	NAME = 'Burst display'

	SLUG = 'bdisplay'

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
		pygame.display.init()
		pygame.font.init()

		self.font = pygame.font.SysFont("sans", 10)

		self.size = 512, 800
		self.screen = pygame.display.set_mode(self.size)

		self.back = pygame.Surface(self.size)
		self.line = pygame.Surface((self.size[0], 1))

		self.cmap = get_cmap('magma')

		self.t = np.empty(self.size[1])
		self.t[:] = 0

		super().run(opts)

	def work(self, msg):
		if 'data' in msg:
			self.spectrum_update(msg)

			if np.random.random() < .1:
				self.add_burst({'burst':{
					'tstart': self.t[700],
					'tstop': self.t[703],
					'fc': np.random.random()*512,
					'bw': 3,
					'text': 'aaa\nbbbb\ncc'}})
		elif 'burst' in msg:
			self.add_burst(msg)

	def add_burst(self, msg):
		burst = msg['burst']
		RED = (255, 0, 0)

		def gety(t):
			return int(np.round(np.interp(t, self.t, np.arange(len(self.t)))))

		y1 = gety(burst['tstart'])
		y2 = gety(burst['tstop'])

		x1 = int(burst['fc'] - burst['bw']/2)
		x2 = int(burst['fc'] + burst['bw']/2)

		r = pygame.Rect(x1, y1, x2-x1, y2-y1)
		pygame.draw.rect(self.back, RED, r, 1)

		mw = -1
		texts = []
		for t in burst['text'].split('\n'):
			text = self.font.render(t, True, RED)
			mw = max(text.get_size()[0], mw)
			texts.append(text)

		x = min(x2, self.size[0]-mw)
		y = y2
		for text in texts:
			self.back.blit(text, (x, y))
			y += 10

	def spectrum_update(self, msg):
		x = np.array(msg['data'])

		self.t[:-1] = self.t[1:]
		self.t[-1] = msg['timestamp']

		vmin = -130
		vmax = -100

		v = ((x - vmin) / (vmax-vmin))[::2]
		v = v.clip(0, 1)
		#v = np.array(255*v, dtype=int)

		a = pygame.surfarray.pixels3d(self.line)

		b = np.empty((v.shape[0], 3))
		for i in range(v.shape[0]):
			b[i,:] = self.cmap(v[i])[:3]

		b *= 255
		a[:,0,:] = b

		del a

		#print(s.get_size())

		self.back.scroll(dy=-1)
		#self.back.blit(s, dest=(0,self.size[1]-1))
		self.back.blit(self.line, dest=(0,self.size[1]-1))
		self.screen.blit(self.back, dest=(0,0))
		pygame.display.flip()
