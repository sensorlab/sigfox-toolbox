from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import argparse
from importlib import import_module

class HTTPRequestHandler(BaseHTTPRequestHandler):
	def do_POST(self):
		length = int(self.headers.get('content-length'))

		s = self.rfile.read(length)
		msg = json.loads(s.decode('utf8'))

		resp = self.server.f(msg)

		self.send_response(200)
		self.end_headers()
		self.log_request()

		s = json.dumps(resp)
		self.wfile.write(s.encode('utf8'))

class SFNRBaseNode(object):
	TEMPLATE = "httprequest"

	def run(self, opts):
		print("Running node '%s' on port %d" % (self.SLUG, self.PORT))
		print("Options: %s" % (opts,))
		self.run_server()

	def run_server(self):
		server_address = ('localhost', self.PORT)
		httpd = HTTPServer(server_address, HTTPRequestHandler)
		httpd.f = self.work
		httpd.serve_forever()

	@classmethod
	def install(cls):
		#node_dir = os.path.join(os.environ['HOME'], ".node-red/nodes")
		node_dir = os.path.join(os.environ['HOME'], "node_modules/node-red/nodes/sfnr")

		try:
			os.mkdir(node_dir)
		except OSError:
			pass

		for ext in ['js', 'html']:
			in_path = "templates/%s.%s.in" % (cls.TEMPLATE, ext)
			out_path = os.path.join(node_dir, "%s.%s" % (cls.SLUG, ext))

			cls._install_template(in_path, out_path)

	@classmethod
	def _install_template(cls, in_path, out_path):
		t = open(in_path).read()

		t = t % { 'port': cls.PORT,
			  'name': cls.NAME,
			  'slug': cls.SLUG,
			  'category': cls.CATEGORY,
			  'desc': cls.DESC }

		print("writing %s" % (out_path,))

		open(out_path, 'w').write(t)

def main():
	parser = argparse.ArgumentParser(description="Node-RED block starter")
	parser.add_argument("-o", "--option", metavar="KEY=VAL", action='append', nargs="?")
	parser.add_argument("node", metavar="NODE", nargs=1)

	args = parser.parse_args()

	opts = {}
	if args.option:
		for opt in args.option:
			key, val = opt.split('=')
			opts[key] = val

	m = import_module("sfnr.nodes." + args.node[0])
	node = m.SFNRNode()

	assert args.node[0] == node.SLUG

	node.run(opts)

if __name__ == "__main__":
	main()
