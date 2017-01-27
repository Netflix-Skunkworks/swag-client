# -*- coding: utf-8 -*-

import pytest

from swag_client import InvalidSWAGDataException
from swag_client.swag import get_all_accounts, get_by_name, get_by_aws_account_number
from tests.conf import SWAG_BUCKET, ACCOUNTS_FILE_PATH, BAD_ACCOUNTS_FILE_PATH, SWAG_BUCKET_REGION


def test_schema():
    from swag_client.swag import SWAGSchema
    data = {
        "accounts": [
            {
                "bastion": "testaccount.net",
                "metadata": {
                    "s3_name": "testaccounts3",
                    "cloudtrail_index": "cloudtrail_testaccount[yyyymm]",
                    "cloudtrail_kibana_url": "http://testaccount.cloudtrail.dashboard.net",
                    "email": "testaccount@test.net",
                    "account_number": "012345678910"
                },
                "schema_version": 1,
                "owners": [
                    "admins@test.net"
                ],
                "ours": True,
                "description": "LOL, Test account",
                "cmc_required": False,
                "tags": [
                    "testing"
                ],
                "id": "aws-012345678910",
                "name": "testaccount",
                "type": "aws",
                "alias": [
                    "test",
                ],
                "services": {
                    "rolliepollie": {
                        "enabled": True
                    },
                    "awwwdit": {
                        "enabled": True
                    }
                }
            }
        ]
    }

    accounts_dict = SWAGSchema(strict=True).load(data)

    assert accounts_dict

    data = {
        "data": [{
            "not valid": "( ͡° ͜ʖ ͡°)"
        }]
    }

    with pytest.raises(InvalidSWAGDataException):
        SWAGSchema(strict=True).load(data)


def test_get_all_accounts(swag_bucket):
    data = get_all_accounts(SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH)
    assert len(data["accounts"]) == 2

    with pytest.raises(InvalidSWAGDataException):
        get_all_accounts(SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=BAD_ACCOUNTS_FILE_PATH)

    data = get_all_accounts(SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH, **{'owners': ["someadmin@test.net"]})
    assert len(data["accounts"]) == 1

    data = get_all_accounts(SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH, bastion="test2.net")
    assert len(data["accounts"]) == 1

    data = get_all_accounts(SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH, **{'metadata': {"s3_name": "testaccount2"}})
    assert len(data["accounts"]) == 1

def test_get_by_name(swag_data):
    # Test getting account named: "test1@test"
    account = get_by_name("test1@test", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH)
    assert account["name"] == "test1@test"

    # Test by getting account named: "test2@test"
    account = get_by_name("test2@test", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH)
    assert account["name"] == "test2@test"

    # Test by getting account that does not exist:
    assert not get_by_name("( ͡° ͜ʖ ͡°)", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH)

    # With alias
    account = get_by_name("testaccnt1", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH, alias=True)
    assert account["metadata"]["account_number"] == "012345678910"

    # Test exception:
    with pytest.raises(InvalidSWAGDataException):
        get_by_name("( ͡° ͜ʖ ͡°)", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=BAD_ACCOUNTS_FILE_PATH)


def test_get_by_aws_account_number(swag_data):
    # Test getting account # 012345678910
    account = get_by_aws_account_number("012345678910", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH)
    assert account["name"] == "test1@test"

    # Test by getting account # 109876543210
    account = get_by_aws_account_number("109876543210", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH)
    assert account["name"] == "test2@test"

    # Test by getting account that does not exist:
    assert not get_by_aws_account_number("( ͡° ͜ʖ ͡°)", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=ACCOUNTS_FILE_PATH)

    # Test exception:
    with pytest.raises(InvalidSWAGDataException):
        get_by_aws_account_number("( ͡° ͜ʖ ͡°)", SWAG_BUCKET, region=SWAG_BUCKET_REGION, json_path=BAD_ACCOUNTS_FILE_PATH)

