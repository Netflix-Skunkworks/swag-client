"""
.. module:: swag_client.swag
    :platform: Unix
.. author:: Kevin Glisson (kglisson@netflix.com)
.. author:: Mike Grima (mgrima@netflix.com)
"""
import boto3
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from marshmallow import Schema, fields, validates_schema
from marshmallow.exceptions import ValidationError
from marshmallow.validate import Length, Validator, OneOf

# Set up a CacheManager for caching SWAG data:
from swag_client import InvalidSWAGDataException

CACHE_OPTS = {
    'cache.type': "memory",
    'cache.lock_dir': 'swag_lock',
}
cache = CacheManager(**parse_cache_config_options(CACHE_OPTS))


def validate_fqdn(n):
    if '.' not in n:
        raise ValidationError("{0} is not a FQDN".format(n))


class IsDigit(Validator):
    def __call__(self, value):
        if not value.isdigit():
            raise ValidationError("Must be a string of digits: {}".format(value))
        return True


# These are nested fields and are validated based on the 'type'
# specified
class AWSAccountSchema(Schema):
    account_number = fields.String(required=True, validate=Length(max=12, min=12))  # equal keyword not yet available in mainline marshmallow
    cloudtrail_index = fields.String(required=True)
    cloudtrail_kibana_url = fields.String()
    s3_name = fields.String(required=True)
    email = fields.Email(required=True)


class GoogleProjectSchema(Schema):
    project_id = fields.String(required=True, validate=Length(max=30))
    project_number = fields.Integer(required=True)
    project_name = fields.String(required=True)


TYPES = {'aws': AWSAccountSchema, 'gcp': GoogleProjectSchema}


# Here are define top level fields that every account would need
class AccountSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    type = fields.String(required=True, validate=OneOf(TYPES.keys()))
    metadata = fields.Dict(required=True)
    tags = fields.List(fields.String())
    services = fields.Dict()
    cmc_required = fields.Boolean(required=True)
    description = fields.String(required=True)
    owners = fields.List(fields.Email(required=True), required=True)
    alias = fields.List(fields.String(), required=True)
    bastion = fields.String(validate=validate_fqdn)

    # Set to True if your company owns the account.
    # Set to False if this is a partner account your apps may need to know about.
    ours = fields.Boolean(required=True)

    schema_version = fields.Integer(required=True)

    @validates_schema
    def validate_metadata(self, data):
        metadata = TYPES[data['type']](many=True, strict=True).load([data['metadata']])


class SWAGSchema(Schema):
    accounts = fields.Nested(AccountSchema, many=True, required=True)

    def handle_error(self, exc, data):
        """Log and raise our custom exception when (de)serialization fails."""
        raise InvalidSWAGDataException(exc.messages)


def upload(data, bucket, region, json_path):
    """
    Uploads a given file to SWAG
    :return:
    """
    accounts = SWAGSchema(strict=True).dumps(data)

    s3 = boto3.cli("s3", region_name=region)
    s3.put_object(Bucket=bucket, Key=json_path, Body=accounts)


@cache.cache(expire=3600)
def fetch(bucket, region, json_path):
    s3 = boto3.client("s3", region_name=region)
    object = s3.get_object(Bucket=bucket, Key=json_path)

    return object["Body"].read().decode()


def get_by_name(account_name, bucket, region='us-west-2', json_path='accounts.json', alias=None):
    """
    Given an account name, attempts to retrieve associated account info.

    This will use cached data from SWAG. If the cache has expired, then it will reach out to SWAG to
    grab more data. This will raise all of the exceptions that get_all_accounts() raises.
    :param alias:
    :param account_name:
    :return:
    """
    for account in get_all_accounts(bucket, region, json_path)["accounts"]:
        if "aws" in account["type"]:
            if account["name"] == account_name:
                return account
            elif alias:
                for a in account["alias"]:
                    if a == account_name:
                        return account


def get_by_aws_account_number(account_number, bucket, region='us-west-2', json_path='accounts.json'):
    """
    Given an account number (or ID), attempts to retrieve associated account info

    This will use cached data from SWAG. If the cache has expired, then it will reach out to SWAG to
    grab more data. This will raise all of the exceptions that get_all_accounts() raises.
    :param account_number:
    :return:
    """
    for account in get_all_accounts(bucket, region, json_path)["accounts"]:
        if "aws" in account["type"]:
            if account["metadata"]["account_number"] == account_number:
                return account


def is_sub_dict(sub_dict, dictionary):
    for key in sub_dict.keys():
        if key not in dictionary:
            return False
        if (type(sub_dict[key]) is not dict) and (sub_dict[key] != dictionary[key]):
            return False
        if (type(sub_dict[key]) is dict) and (not is_sub_dict(sub_dict[key], dictionary[key])):
            return False
    return True


def get_all_accounts(bucket, region='us-west-2', json_path='accounts.json', **filters):
    """
    Fetches all the accounts from SWAG. This will raise exceptions related
    to botocore, as well as exceptions regarding validation errors.

    :return:
    """

    accounts_obj = fetch(bucket, region, json_path)
    accounts_dict, errors = SWAGSchema(strict=True).loads(accounts_obj)
    accounts_dict["accounts"] = [account for account in accounts_dict["accounts"] if is_sub_dict(filters, account)]
    return accounts_dict

