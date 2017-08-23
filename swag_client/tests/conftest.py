import os

import boto3
import pytest
import tempfile
from moto import mock_s3, mock_dynamodb2


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
def s3_bucket_name():
    mock_s3().start()

    s3 = boto3.client('s3')
    s3.create_bucket(Bucket='swag.test.backend')
    yield 'swag.test.backend'
    mock_s3().stop()


@pytest.yield_fixture(scope='function')
def dynamodb_table():
    mock_dynamodb2().start()
    resource = boto3.resource('dynamodb', region_name='us-east-1')

    table = resource.create_table(
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
    mock_dynamodb2().stop()


