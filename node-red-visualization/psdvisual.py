from bokeh.models import ColumnDataSource
from bokeh.palettes import Magma256, Viridis256
from bokeh.plotting import curdoc, figure, gridplot

from functools import partial
import numpy as np
from PIL import Image
from sfnr.core import SFNRBaseNode
from sfnr.config.sensing import Ns, fs, fc, fc_corr, f_min, f_max, Nselector
from threading import Thread
from time import time

# real central frequency of the sensor, with correction applied.
fc_real = fc - fc_corr

# Size of the real FFT
Ws = Ns//2+1

# central frequencies of FFT bins
bin_to_f = fc_real - fs/4 + np.arange(Ws)*fs/Ns

# Range of the sensor
f_sens_min = bin_to_f[0]
f_sens_max = bin_to_f[Ws-1]

def f_to_bin(f):
	return int(round((f - fc_real + fs/4)*Ns/fs))

bin_min = f_to_bin(f_min)
bin_max = f_to_bin(f_max) + 1

Ws2 = bin_max - bin_min

class FancyPlot(object):
	PLOT_HEIGHT = 200
	def get_figure(self):
		return self.fig

	def update(self, msg):
		pass


class BasebandPlot(FancyPlot):

	def create(self):
		self.fig = figure(title="Baseband", x_range=(0, Ns), y_range=(1024, 3072),
				plot_height=self.PLOT_HEIGHT)

		x = np.arange(Ns/fs*1e6)
		y = np.zeros(Ns)

		self.cds = ColumnDataSource(data=dict(x=x, y=y))

		self.fig.line(x='x', y='y', source=self.cds)

		self.fig.xaxis.axis_label = "time [us]"
		self.fig.yaxis.axis_label = "ADC samples"

	def update(self, msg):
		if 'data' not in msg:
			return

		y = np.array(msg['data'])
		self.cds.data['y'] = y


class PSDPlot(FancyPlot):

	def create(self):
		y_min = -100
		y_max = -20

		self.fig = figure(title="Power spectral density (PSD)",
				x_range=(f_sens_min/1e6, f_sens_max/1e6),
				y_range=(y_min, y_max),
				plot_height=self.PLOT_HEIGHT)

		self.fig.quad(top=[y_max], bottom=[y_min],
				left=[f_min/1e6], right=[f_max/1e6],
				color="#c0c0c0", alpha=0.5)

		x = bin_to_f/1e6
		y = np.zeros(Ws)

		self.cds = ColumnDataSource(data=dict(x=x, y=y))

		self.fig.line(x='x', y='y', source=self.cds)

		self.fig.xaxis.axis_label = "frequency [MHz]"
		self.fig.yaxis.axis_label = "power [dB]"

	def update(self, msg):
		if 'fft' not in msg:
			return

		y = 10. * np.log10(np.array(msg['fft']))
		self.cds.data['y'] = y

class Intermission(FancyPlot):

	def create(self):

		self.fig = figure(x_range=(f_sens_min/1e6, (f_sens_max/1e6)),
				y_range=(0, 1),
				plot_height=int(self.PLOT_HEIGHT/4))

		self.fig.line([f_sens_min/1e6, f_sens_min/1e6, f_min/1e6, f_min/1e6],
				[0, .2, .8, 1], color='black', line_width=2)
		self.fig.line([f_sens_max/1e6, f_sens_max/1e6, f_max/1e6, f_max/1e6],
				[0, .2, .8, 1], color='black', line_width=2)

		self.fig.xaxis.visible = False
		self.fig.yaxis.visible = False
		self.fig.grid.visible = False
		self.fig.outline_line_color = 'white'


class WaterfallPlot(FancyPlot):

	HIST_SIZE = 100

	def __init__(self):

		self.img_w = min(200, Ws)
		self.img_h = 100

		self.hist = np.zeros((self.HIST_SIZE, Ws2))
		#self.tshist = time() + np.arange(self.HIST_SIZE)*.5

	def _get_image(self):
		    i = Image.fromarray(10.*np.log10(self.hist))
		    i2 = i.resize((self.img_w, self.img_h), Image.ANTIALIAS)
		    return np.asarray(i2)

	def create(self):
		self.cds = ColumnDataSource(data=dict(
			x=[f_min/1e6], dw=[(f_max - f_min)/1e6],
			y=[0], dh=[1],
			image=[self._get_image()]))

		self.fig = figure(title="PSD history",
				plot_height=self.PLOT_HEIGHT,
				x_range=(f_min/1e6, f_max/1e6),
				y_range=(0, 1),
				)
		self.fig.image(image='image', x='x', y='y', dw='dw', dh='dh',
				palette=Magma256, source=self.cds)

		self.fig.yaxis.axis_label = "time"
		self.fig.yaxis.major_label_text_font_size = "0pt"

		self.fig.xaxis.axis_label = "frequency [MHz]"

	def update(self, msg):

		if 'fft' not in msg or 'timestamp' not in msg:
			return

		w = np.array(msg['fft'])

		w0 = w[bin_min:bin_max]

		self.hist = np.roll(self.hist, 1, axis=0)
		self.hist[0,:] = w0
		self.cds.data['image'] = [self._get_image()]

		#self.tshist = np.roll(self.tshist, 1, axis=0)
		#self.tshist[0] = msg['timestamp']
		#self.cds.data['dh'] = [self.tshist[-1] - self.tshist[0]]

class MeanPSD(FancyPlot):

	def create(self):
		y_min = -100
		y_max = -20

		self.fig = figure(title="Mean PSD and candidate channels for transmission",
				x_range=(f_min/1e6, f_max/1e6),
				y_range=(y_min, y_max),
				plot_height=self.PLOT_HEIGHT)

		x = np.arange(Nselector)
		y = (y_max + y_min)/2 * np.ones(Nselector)

		w = 100/1e6
		h = (y_max - y_min)

		self.cds_f_tx = ColumnDataSource(data=dict(x=x, y=y))

		self.fig.rect(x='x', y='y', width=w, height=h, color="#00ff00", alpha=.7,
				source=self.cds_f_tx)


		x = bin_to_f[bin_min:bin_max]/1e6
		y = np.zeros(Ws2)

		self.cds_meanpsd = ColumnDataSource(data=dict(x=x, y=y))

		self.fig.line(x='x', y='y', color='green', source=self.cds_meanpsd)

		self.fig.xaxis.axis_label = "frequency [MHz]"
		self.fig.yaxis.axis_label = "power [dB]"

	def update(self, msg):

		if 'f_tx' in msg:
			f_tx = np.array(msg['f_tx'])/1e6
			self.cds_f_tx.data['x'] = f_tx

		if 'meanpsd' in msg:
			meanpsd = 10.*np.log10(np.array(msg['meanpsd']))
			self.cds_meanpsd.data['y'] = meanpsd[bin_min:bin_max]


class SFNRNode(SFNRBaseNode):
	PORT = 7211

	NAME = 'PSD visualization'

	SLUG = 'visual'

	DESC = 'Example node'

	CATEGORY = 'sensing'

	def __init__(self, doc, cls_list):
		self.doc = doc

		self.plots = []
		figures = []
		for cls in cls_list:
			plot = cls()
			plot.create()

			figures.append(plot.get_figure())
			self.plots.append(plot)

		gp = gridplot(figures, ncols=1)
		self.doc.add_root(gp)

	def update(self, msg):
		for plot in self.plots:
			plot.update(msg)

	def work(self, msg):
		self.doc.add_next_tick_callback(partial(self.update, msg))

		return {}

def main():
	doc = curdoc()

	cls_list = [
			BasebandPlot,
			PSDPlot,
			Intermission,
			WaterfallPlot,
			MeanPSD
	]

	node = SFNRNode(doc, cls_list)

	opts = {}
	thread = Thread(target=node.run, args=(opts,))
	thread.start()

main()
