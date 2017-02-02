from setuptools import setup
from setuptools.command.install import install as _install
import glob
import importlib
import os.path

class install(_install):
	def run(self):
		_install.run(self)

		for path in glob.glob("nodes/*.py"):

			name = os.path.basename(path)
			name = name.replace(".py", "")

			if name.startswith("_"):
				continue

			m = importlib.import_module("nodes." + name)
			m.SFNRNode.install()

setup(
    name='sfnr-visual',

    version='1.0.0',

    description='Support for Node-RED Python blocks',

    author='Tomaz Solc',
    author_email='tomaz.solc@ijs.si',

    packages=[],

    install_requires=[
	    'sfnr',
	    'sfnr-sensing',
	    'bokeh~=0.12',
	    'numpy',
            'pillow',
    ],

    cmdclass={'install': install}
)
