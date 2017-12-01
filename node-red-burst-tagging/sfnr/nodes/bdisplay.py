from sfnr.core import SFNRBaseNode
import sfnr.config.sigfox as cfg
import numpy as np
import pygame
from matplotlib.cm import get_cmap

class InfoQueueEntry(object):
	def __init__(self, ib, y):
		self.ib = ib
		self.y = y
		self.h = ib.surface.get_size()[1]

class InfoQueue(object):
	VMARGIN = 10
	def __init__(self, back, x):
		self.q = []
		self.back = back
		self.h = back.get_size()[1]
		self.x = x
		self.ceiling = 0

	def add(self, ibe):
		self.q.append(ibe)
		self.q.sort(key=lambda ibe:(ibe.ib.prio, ibe.y))

	def scroll(self):
		q2 = []
		for ibe in self.q:
			if self.ceiling < ibe.y:
				y = ibe.y
			else:
				y = self.ceiling

			if y + ibe.h < self.h:
				ibe.ib.blit(self.back, self.x, y)

				self.ceiling = y + ibe.h + self.VMARGIN
			else:
				ibe.y -= 1
				ibe.ib.anchor = (ibe.ib.anchor[0], ibe.ib.anchor[1] - 1)

				if ibe.y > self.h*3/4:
					q2.append(ibe)

		self.ceiling -= 1
		self.q = q2

class InfoBlock2(object):
	def __init__(self, surface, anchor, color, prio):
		self.surface = surface
		self.anchor = anchor
		self.color = color
		self.prio = prio

	def blit(self, back, x, y):
		back.blit(self.surface, (x,y))

		w, h = self.surface.get_size()

		ax, ay = self.anchor

		if x < ax:
			x2 = x+w
			x3 = x2 + 2
		else:
			x2 = x
			x3 = x2 - 2

		pygame.draw.line(back, self.color, (ax, ay), (x3, y+h//2))
		pygame.draw.line(back, self.color, (x3, y), (x3, y+h))


class InfoBlock(object):
	LINE_HEIGHT = 10
	def __init__(self, text, font, color):

		lines = text.split('\n')

		w = 0
		h = 0

		surfaces = []
		for line in lines:
			surface = font.render(line, True, color)

			sw, sh = surface.get_size()
			w = max(sw, w)
			h += self.LINE_HEIGHT

			surfaces.append(surface)


		self.surface = pygame.Surface((w, h))
		self.surface.set_alpha(color[3])

		y = 0
		for surface in surfaces:
			self.surface.blit(surface, (0, y))
			y += self.LINE_HEIGHT

class SFNRNode(SFNRBaseNode):

	PORT = 7215

	NAME = 'Burst display'

	SLUG = 'bdisplay'

	DESC = """
<p>Show a real-time waterfall diagram, with an overlay of recognized burst and associated meta-data. The visualization is displayed in a separate window (shown when you run the back-end). This node serves as an input port for the data to be visualized.</p>

<p>Input for spectrum data to be displayed on the waterfall diagram in the background:</p>

<pre>
{
    'data': [ <i>RSSI in dBm</i>, ... ]
    'timestamp': <i>timestamp</i>
}
</pre>

<p>Input for burst overlay:</p>

<pre>
{
    'bursts': [
        {
	    'tstart': <i>burst start time</i>,
	    'tstop': <i>burst stop time</i>,
	    'fc': <i>burst central frequency</i>,
	    'bw': <i>burst bandwidth</i>,
	    'bold': <i>whether the burst should be emphasized on display</i>,
	    'text': <i>text to show with the burst</i>
	},
	...
    ]
}
</pre>

<p>To run back-end for this node, run the following:</p>

<pre>
sfnr bdisplay
</pre>"""

	CATEGORY = "sigfox"
	K = 2

	def run(self, opts):
		pygame.display.init()
		pygame.font.init()

		self.font = pygame.font.SysFont("sans", 10)

		self.margin = 200

		self.size = cfg.M//self.K, 800
		self.dsize = (self.size[0]+self.margin*2, self.size[1])
		self.screen = pygame.display.set_mode(self.dsize)
		pygame.display.set_caption("Burst display")

		self.back = pygame.Surface(self.dsize)
		self.info = pygame.Surface(self.dsize, pygame.SRCALPHA)
		self.info.fill((0, 0, 0, 0))
		self.info.set_alpha(128)
		self.line = pygame.Surface((self.dsize[0], 1))

		self.cmap = get_cmap('magma')

		self.t = np.empty(self.size[1])
		self.reset_timeline()

		super().run(opts)

	def reset_timeline(self):
		self.t[:] = 0

		self.l_texts = InfoQueue(self.info, 20)
		self.r_texts = InfoQueue(self.info, self.dsize[0] - self.margin + 20)

	def work(self, msg):
		if 'data' in msg:
			self.r_texts.scroll()
			self.l_texts.scroll()

			self.spectrum_update(msg)

			#if np.random.random() < .1:
			#	self.add_burst({'burst':{
			#		'tstart': self.t[700],
			#		'tstop': self.t[703],
			#		'fc': np.random.random()*512,
			#		'bw': 3,
			#		'text': 'aaa\nbbbb\ncc'}})
		elif 'bursts' in msg:
			for burst in msg['bursts']:
				self.add_burst(burst)

	def add_burst(self, burst):
		if burst['bold']:
			color = (255, 0, 0, 200)
			prio = 0
		else:
			color = (255, 0, 0, 120)
			prio = 1

		def gety(t):
			return int(np.round(np.interp(t, self.t, np.arange(len(self.t)))))

		y1 = gety(burst['tstart'])
		y2 = gety(burst['tstop'])

		x1 = cfg.freq_to_bin(burst['fc'] - burst['bw']/2)//self.K + self.margin
		x2 = cfg.freq_to_bin(burst['fc'] + burst['bw']/2)//self.K + self.margin

		r = pygame.Rect(x1, y1, x2-x1, y2-y1)
		pygame.draw.rect(self.info, color, r, 1)

		infoblock = InfoBlock(burst['text'], self.font, color)

		if (x1+x2)/2 > self.margin + self.size[0]/2:
			ib2 = InfoBlock2(infoblock.surface, (x2, (y1+y2)/2), color, prio)
			self.r_texts.add(InfoQueueEntry(ib2, y2))
		else:
			ib2 = InfoBlock2(infoblock.surface, (x1, (y1+y2)/2), color, prio)
			self.l_texts.add(InfoQueueEntry(ib2, y2))

	def spectrum_update(self, msg):
		# Reset timeline if timestamps changed significantly. Prevents
		# garbled display when e. g. source of spectrum data was
		# restarted
		if abs(self.t[-1] - msg['timestamp']) > 100:
			self.reset_timeline()

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
		a[self.margin:-self.margin,0,:] = b

		del a

		#print(s.get_size())

		self.back.scroll(dy=-1)
		self.info.scroll(dy=-1)
		pygame.draw.line(self.info, (0, 0, 0, 0), (0, self.dsize[1]-1), (self.dsize[0]-1, self.dsize[1]-1))
		#self.back.blit(s, dest=(0,self.size[1]-1))
		self.back.blit(self.line, dest=(0,self.size[1]-1))
		self.screen.blit(self.back, dest=(0,0))
		self.screen.blit(self.info, dest=(0,0))
		pygame.display.flip()
