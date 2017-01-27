import os

import boto3
import pytest
from moto import mock_s3
from swag_client.swag import get_all_accounts
from tests.conf import SWAG_BUCKET, ACCOUNTS_FILE_PATH, BAD_ACCOUNTS_FILE_PATH, SWAG_BUCKET_REGION


def get_json(file):
    cwd = os.path.dirname(os.path.realpath(__file__))
    awwwdit_path = os.path.join(cwd, 'templates/{}'.format(file))

    with open(awwwdit_path, 'r') as ap:
        return ap.read()


@pytest.yield_fixture(scope="function")
def swag_bucket():
    mock_s3().start()

    s3 = boto3.client('s3')
    s3.create_bucket(Bucket=SWAG_BUCKET)

    s3.put_object(Bucket=SWAG_BUCKET, Key=ACCOUNTS_FILE_PATH, Body=get_json("swag_test.json"))
    s3.put_object(Bucket=SWAG_BUCKET, Key=BAD_ACCOUNTS_FILE_PATH, Body=get_json("bad_swag_test.json"))

    yield s3
    mock_s3().stop()


@pytest.fixture(scope="function")
def swag_data(swag_bucket):
    return get_all_accounts(SWAG_BUCKET, SWAG_BUCKET_REGION, ACCOUNTS_FILE_PATH)

