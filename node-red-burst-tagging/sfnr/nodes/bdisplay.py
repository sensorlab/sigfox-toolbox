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

		self.size = 512, 800
		self.screen = pygame.display.set_mode(self.size)

		self.back = pygame.Surface(self.size)
		self.line = pygame.Surface((self.size[0], 1))

		self.cmap = get_cmap('magma')

		super().run(opts)

	def work(self, msg):
		x = np.array(msg['data'])

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
