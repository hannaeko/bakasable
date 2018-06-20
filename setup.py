import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

setup(
    name='Bakasable',
    version='0.1',
    description='Peer to peer multiplayer sandbox game based on NDN.',
    long_description=README,
    license="GPLv3",
    author='BlackSponge <Gaël Berthaud-Müller>',
    author_email='blacksponge@tuta.io',
    url='https://github.com/blacksponge/bakasable',
    package_dir={'bakasable': 'src'},
    packages=['bakasable'],
    zip_safe=False,
    install_requires=[
        'PyNDN',
        'noise',
        'sortedcontainers'
    ],
    entry_points={
        'console_scripts': [
            'bakasable   = bakasable.main:main'
        ]
    }
)
