import os

import boto3
import pytest
import tempfile

from mock import patch
from moto import mock_s3, mock_dynamodb2


@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture(scope='function')
def retry():
    """Mock the retry library so that it doesn't retry."""
    def mock_retry_decorator(*args, **kwargs):
        def retry(func):
            return func
        return retry

    patch_retry = patch('retrying.retry', mock_retry_decorator)
    yield patch_retry.start()

    patch_retry.stop()


@pytest.fixture(scope='function')
def s3(aws_credentials, retry):
    with mock_s3():
        yield boto3.client('s3')


@pytest.fixture(scope='function')
def dynamodb(aws_credentials):
    with mock_dynamodb2():
        yield boto3.resource('dynamodb', region_name='us-east-1')


@pytest.fixture(scope='function')
def temp_file_name():
    """A temporary file for function scope."""
    with tempfile.NamedTemporaryFile(delete=True) as f:
        yield f.name


@pytest.fixture(scope='session')
def vector_path():
    cwd = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(cwd, 'vectors')


@pytest.yield_fixture(scope='function')
def s3_bucket_name(s3):
    s3.create_bucket(Bucket='swag.test.backend')
    yield 'swag.test.backend'


@pytest.yield_fixture(scope='function')
def dynamodb_table(dynamodb):
    table = dynamodb.create_table(
        TableName='accounts',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        })

    table.meta.client.get_waiter('table_exists').wait(TableName='accounts')
    yield
