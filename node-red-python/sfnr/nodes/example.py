from sfnr.core import SFNRBaseNode

class SFNRNode(SFNRBaseNode):
	PORT = 7210

	NAME = 'Example'

	SLUG = 'example'

	DESC = 'Example node'

	CATEGORY = 'examples'

	def work(self, msg):
		msg['greeting'] = 'Hello, world!'
		return msg
