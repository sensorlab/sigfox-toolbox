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
    name='sfnr',

    version='1.0.0',

    description='Node-RED block starter',

    author='Tomaz Solc',
    author_email='tomaz.solc@ijs.si',

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'sfnr=sfnr:main',
        ],
    },

    install_requires=['numpy'],

    cmdclass={'install': install}
)
