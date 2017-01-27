"""
SWAG Client
===========

Is a python client to interface with the SWAG service.
It also provides some helpful functions for dealing with accounts (aws or otherwise)
"""
import sys
import os.path

from setuptools import setup, find_packages

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

sys.path.insert(0, ROOT)

about = {}
with open(os.path.join(ROOT, "swag_client", "__about__.py")) as f:
    exec(f.read(), about)


install_requires = [
    'requests==2.9.1',
    'marshmallow>=2.6.0',
    'inflection==0.3.1',
    'boto3>=1.2.6',
    'tabulate>=0.7.5',
    'beaker>=1.8.0',
    'docopt==0.6.2'
]

tests_require = [
    'pytest==2.8.3',
    'moto>=0.4.23',
]

setup(
    name=about["__title__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    url=about["__uri__"],
    description=about["__summary__"],
    long_description=open(os.path.join(ROOT, 'README.rst')).read(),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_require
    },
    entry_points={
        'console_scripts': [
            'swag = swag_client.cli:main',
        ]
    },
    keywords = ['aws', 'account_management']
)

