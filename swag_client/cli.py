"""
CLI for accessing and manipulating the SWAG account file.

USAGE:
    swag upload <bucket> [<region>] [<filename>]
    swag validate [<filename>]
    swag list <bucket> [<region>]
"""
import os
import sys

from docopt import docopt

from tabulate import tabulate
from .swag import get_all_accounts, upload, SWAGSchema, InvalidSWAGDataException


## magic to find the local path
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def get_file_data(args):
    if args.get('<filename>'):
        file_path = args['<filename>']
    else:
        file_path = '{}/accounts.json'.format(os.path.dirname(os.path.realpath(__file__)))

    with open(file_path, 'r') as f:
        file_data = f.read()

    return file_data


def main():
    args = docopt(__doc__)
    bucket = args.get('<bucket>')
    region = args.get('<region>', 'us-east-1')

    if args.get('validate'):
        file_data = get_file_data(args)
        try:
            SWAGSchema(strict=True).loads(file_data)
        except InvalidSWAGDataException as e:
            print("Validation failed.")

    elif args.get('upload'):
        file_data = get_file_data(args)

        try:
            upload(file_data, bucket, region, '/accounts.json')
        except InvalidSWAGDataException as e:
            print("Unable to upload, validation failed.")

    elif args.get('list'):
        print(table(bucket))


def table(bucket):
    """
    Takes the SWAG json file and renders it in an easy to digest
    table
    :return:
    """
    _table = [[result['name'], result['metadata'].get('account_number')] for result in get_all_accounts(bucket=bucket).get('accounts')]
    return tabulate(_table, headers=["Account Name", "Account Number"])
