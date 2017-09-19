from setuptools import setup, find_packages
from setuptools.command.install import install as _install
import glob
import importlib
import os.path

class install(_install):
	def run(self):
		_install.run(self)

		for path in glob.glob("sfnr/nodes/*.py"):

			name = os.path.basename(path)
			name = name.replace(".py", "")

			if name.startswith("_"):
				continue

			m = importlib.import_module("sfnr.nodes." + name)
			m.SFNRNode.install()

setup(
    name='sfnr-burst',

    version='1.0.0',

    description='Node-RED blocks for burst tagging',

    author='Tomaz Solc',
    author_email='tomaz.solc@ijs.si',

    packages=find_packages(),

    namespace_packages=['sfnr', 'sfnr.nodes'],

    install_requires=['sfnr', 'numpy', 'pygame', 'matplotlib'],

    cmdclass={'install': install}
)
