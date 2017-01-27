swag_client
===========

.. image:: http://img.shields.io/pypi/v/swag-client.svg?style=flat
    :target: https://pypi.python.org/pypi/swag-client/
    :alt: Pypi

.. image:: https://travis-ci.org/Netflix-Skunkworks/swag-client.svg?branch=master
    :target: https://travis-ci.org/Netflix-Skunkworks/swag-client
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/Netflix-Skunkworks/swag-client/badge.svg?branch=master
    :target: https://coveralls.io/github/Netflix-Skunkworks/swag-client?branch=master
    :alt: Test Coverage
    
.. image:: https://img.shields.io/badge/NetflixOSS-active-brightgreen.svg

Reason:
-------

Remove hardcoded AWS/GCP account numbers from your code.

What is this?
-------------

SWAG is a collection of repositories used to keep track of the metadata describing cloud accounts.  Originally built to store data on AWS, it now also supports GCP.

SWAG is a marshmallow-schema'd JSON file hosted in an S3 bucket.

How we use SWAG:
================

Many applications need to be multi-account aware.  SWAG provides a central place to store information about your accounts and known-friendly accounts.  When bringing up a new account, we simply add the data to SWAG and provide a config role and our infrastructure automatically detects and deploys primitives like IAM Roles to the new account.

Workflow:
---------

We keep a git repository containing the JSON file.  We accept pull requests to this JSON file and have a git-hook to validate the JSON matches the schema.  Once merged, we sync the JSON file to an S3 bucket where all applications can access the data.

We have a separate angularjs project that wraps the JSON file with a simple UI, providing the ability to search by name, account number, etc.

Installation
============

pySWAG is available on pypi::

    pip install swag-client

App Usage
=========

Apps can interact with the library by importing it and calling a method::

    from swag_client.swag import get_all_accounts
    get_all_accounts(bucket='your-swag-bucket').get('accounts')

or to filter by a service tag::

    service = {'services': {'YOURSERVICE': {'enabled': True, 'randomflag': True}}}
    get_all_accounts(bucket='your-swag-bucket', **service).get('accounts')

Permissions required::

    {
        "Action": ["s3:GetObject"],
        "Effect": ["Allow"],
        "Resource: ["arn:aws:s3:::your-swag-bucket/accounts.json"]
    }

CLI Usage
=========

The following CLI options exist::

    swag validate [<filename>]
    
        # Uses Marshmallow to validate the file passed in is in the correct format.
        # <filename> defaults to accounts.json
    
    swag upload <bucket> [<region>] [<filename>]
    
        # Uploads the file to the s3 bucket with key `/accounts.json`.
        # <region> defaults to us-east-1.
        # <filename> defaults to accounts.json
    
    swag list <bucket> [<region>]
    
        # Renders a table with account name and account_number.
        # <region> defaults to us-east-1.

Upload requires special permissions::

    {
        "Action": ["s3:PutObject"],
        "Effect": ["Allow"],
        "Resource: ["arn:aws:s3:::your-swag-bucket/accounts.json"]
    }

Example JSON:
-------------

See sample_accounts.json_

.. _sample_accounts.json: https://github.com/Netflix-Skunkworks/swag-client/blob/master/sample_accounts.json

