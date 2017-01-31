#!/usr/bin/python2.7
from sfnr import SFNRBaseNode

class SFNRNode(SFNRBaseNode):
	PORT = 7212

	NAME = 'Example'

	SLUG = 'example'

	DESC = 'Example node'

	def work(self, msg):
		msg['greeting'] = 'Hello, world!'
		return msg
