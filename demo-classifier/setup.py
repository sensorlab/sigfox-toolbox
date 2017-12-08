from setuptools import setup, find_packages

setup(
    name='demo-classifier',

    version='1.0.0',

    description='Dummy interference classifier',

    author='Tomaz Solc',
    author_email='tomaz.solc@ijs.si',

    packages=find_packages(),

    install_requires=['sfnr', 'numpy', 'matplotlib', 'Pillow' ],

    entry_points={
        'console_scripts': [
            'demo-classifier=classifier:main',
        ],
    },
)
