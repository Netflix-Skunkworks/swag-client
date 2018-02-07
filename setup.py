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
    'marshmallow>=2.13.5,<3.0.0',
    'boto3>=1.4.6',
    'tabulate>=0.7.7',
    'dogpile.cache==0.6.4',
    'click>=6.7',
    'click-log==0.2.1',
    'jmespath>=0.9.3',
    'deepdiff>=3.3.0',
    'retrying>=1.3.3'
]

tests_require = [
    'pytest==3.1.3',
    'moto==1.0.1',
    'coveralls==1.1'
]

setup(
    name=about["__title__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    url=about["__uri__"],
    description=about["__summary__"],
    long_description='See README.md',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_require
    },
    entry_points={
        'console_scripts': [
            'swag-client = swag_client.cli:cli',
        ],
        'swag_client.backends': [
            'file = swag_client.backends.file:FileSWAGManager',
            's3 = swag_client.backends.s3:S3SWAGManager',
            'dynamodb = swag_client.backends.dynamodb:DynamoDBSWAGManager'
        ]
    },
    keywords=['aws', 'account_management']
)
