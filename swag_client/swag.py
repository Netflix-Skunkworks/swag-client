"""
.. module:: swag_client.swag
    :platform: Unix
.. author:: Kevin Glisson (kglisson@netflix.com)
.. author:: Mike Grima (mgrima@netflix.com)
"""
from swag_client.backend import SWAGManager
from swag_client.util import is_sub_dict, deprecated, parse_swag_config_options


@deprecated('This has been deprecated.')
def get_by_name(account_name, bucket, region='us-west-2', json_path='accounts.json', alias=None):
    """Given an account name, attempts to retrieve associated account info."""
    for account in get_all_accounts(bucket, region, json_path)['accounts']:
        if 'aws' in account['type']:
            if account['name'] == account_name:
                return account
            elif alias:
                for a in account['alias']:
                    if a == account_name:
                        return account


@deprecated('This has been deprecated.')
def get_by_aws_account_number(account_number, bucket, region='us-west-2', json_path='accounts.json'):
    """Given an account number (or ID), attempts to retrieve associated account info."""
    for account in get_all_accounts(bucket, region, json_path)['accounts']:
        if 'aws' in account['type']:
            if account['metadata']['account_number'] == account_number:
                return account


@deprecated('This has been deprecated.')
def get_all_accounts(bucket, region='us-west-2', json_path='accounts.json', **filters):
    """Fetches all the accounts from SWAG."""
    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': bucket,
        'swag.bucket_region': region,
        'swag.data_file': json_path,
        'swag.schema_version': 1
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))
    accounts = swag.get_all()
    accounts = [account for account in accounts['accounts'] if is_sub_dict(filters, account)]
    return {'accounts': accounts}




