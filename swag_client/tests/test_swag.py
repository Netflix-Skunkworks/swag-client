import pytest
from moto.dynamodb2 import mock_dynamodb2


@pytest.mark.skip
def test_upgrade_1_to_2():
    from swag_client.schemas.v2 import upgrade, downgrade

    a = {
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

    v2 = upgrade(a)

    assert v2 == {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False,
        'services': [
            {
                'name': 's3',
                'metadata': {
                    'name': 'testaccount3'
                },
                'status': [
                    {
                        'enabled': True,
                        'region': 'all'
                    }
                ]
            },
            {
                'name': 'cloudtrail',
                'metadata': {
                    'kibanaUrl': 'http://testaccount.cloudtrail.dashboard.net',
                    'esIndex': 'cloudtrail_testaccount[yyyymm]'
                },
                'status': [
                    {
                        'enabled': True,
                        'region': 'all'
                    }
                ]
            },
            {
                'name': 'rolliepollie',
                'status': [
                    {
                        'enabled': True,
                        'region': 'all'
                    }
                ]
            },
            {
                'name': 'awwwdit',
                'status': [
                    {
                        'enabled': True,
                        'region': 'all'
                    }
                ]
            }
        ]
    }

    v1 = downgrade(v2)
    assert v1 == a


def test_file_backend_get_all(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v2'
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))
    assert len(swag.get_all()) == 2


def test_file_backend_update(temp_file_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_file': str(temp_file_name)
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)

    account['aliases'] = ['test', 'prod']
    swag.update(account)

    account = swag.get("[?id=='{id}']".format(id=account['id']))
    assert account['aliases'] == ['test', 'prod']


def test_file_backend_delete(temp_file_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_file': str(temp_file_name)
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)
    swag.delete(account)
    assert not swag.get("[?id=='012345678910']")


def test_file_backend_create(temp_file_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_file': str(temp_file_name)
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    assert not swag.get_all()
    item = swag.create(account)
    assert swag.get("[?id=='{id}']".format(id=item['id']))


def test_file_backend_get(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v2'
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    assert swag.get("[?id=='012345678910']")


def test_backend_get_by_name(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v2'
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    assert swag.get_by_name('testaccount')
    assert not swag.get_by_name('test')
    assert swag.get_by_name('test', alias=True)


def test_backend_get_service_name(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v2'
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))
    assert swag.get_service_name('s3', "[?name=='testaccount']") == 'testaccount'


def test_s3_backend_get_all(s3_bucket_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)
    assert len(swag.get_all()) == 1


def test_s3_backend_update(s3_bucket_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)

    account['aliases'] = ['test', 'prod']
    swag.update(account)

    item = swag.get("[?id=='{id}']".format(id=account['id']))

    assert item['aliases'] == ['test', 'prod']


def test_s3_backend_delete(s3_bucket_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678911',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }
    swag.create(account)

    assert len(swag.get_all()) == 2

    swag.delete(account)
    assert len(swag.get_all()) == 1

    #


def test_s3_backend_delete_v1(s3_bucket_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name,
        'swag.schema_version': 1
    }

    swagv1 = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
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

    swagv1.create(account)

    assert len(swagv1.get_all()['accounts']) == 1
    swagv1.delete(account)
    assert len(swagv1.get_all()['accounts']) == 0


def test_s3_backend_create(s3_bucket_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    assert not swag.get_all()
    item = swag.create(account)
    assert swag.get("[?id=='{id}']".format(id=item['id']))


def test_s3_backend_get(s3_bucket_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)
    assert swag.get("[?id=='012345678910']")


@mock_dynamodb2
def test_dynamodb_backend_get():
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.key_type': 'HASH',
        'swag.key_attribute': 'id'
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)
    assert swag.get("[?id=='012345678910']")


@mock_dynamodb2
def test_dynamodb_backend_get_all():
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.key_type': 'HASH',
        'swag.key_attribute': 'id'
    }
    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)
    assert len(swag.get_all()) == 1


@mock_dynamodb2
def test_dynamodb_backend_update():
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.key_type': 'HASH',
        'swag.key_attribute': 'id'
    }
    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)

    account['aliases'] = ['test', 'prod']
    swag.update(account)

    assert swag.get("[?id=='{id}']".format(id=account['id']))


@mock_dynamodb2
def test_dynamodb_backend_delete():
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.key_type': 'HASH',
        'swag.key_attribute': 'id'
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    swag.create(account)
    swag.delete(account)
    assert not swag.get("[?id=='012345678910']")


@mock_dynamodb2
def test_dynamodb_backend_create():
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.key_type': 'HASH',
        'swag.key_attribute': 'id'
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        'aliases': ['test'],
        'contacts': ['admins@test.net'],
        'description': 'LOL, Test account',
        'email': 'testaccount@test.net',
        'environment': 'test',
        'id': '012345678910',
        'name': 'testaccount',
        'owner': 'netflix',
        'provider': 'aws',
        'sensitive': False
    }

    assert not swag.get_all()
    item = swag.create(account)
    assert swag.get("[?id=='{id}']".format(id=item['id']))


# test backwards compatibility
def test_get_all_accounts(s3_bucket_name):
    from swag_client.swag import get_all_accounts

    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name,
        'swag.schema_version': 1
    }

    swagv1 = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
        "bastion": "test2.net",
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
        ]
    }

    swagv1.create(account)

    data = get_all_accounts(s3_bucket_name)
    assert len(data['accounts']) == 1

    data = get_all_accounts(s3_bucket_name,
                            **{'owners': ['admins@test.net']})

    assert len(data['accounts']) == 1

    data = get_all_accounts(s3_bucket_name, bastion="test2.net")
    assert len(data['accounts']) == 1


def test_get_by_name(s3_bucket_name):
    from swag_client.swag import get_by_name

    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name,
        'swag.schema_version': 1
    }

    swagv1 = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
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
        ]
    }

    swagv1.create(account)

    # Test getting account named: 'testaccount'
    account = get_by_name('testaccount', s3_bucket_name)
    assert account['name'] == 'testaccount'

    # Test by getting account that does not exist:
    assert not get_by_name('does not exist', s3_bucket_name)

    # With alias
    account = get_by_name('test', s3_bucket_name, alias=True)
    assert account['metadata']['account_number'] == '012345678910'


def test_get_by_aws_account_number(s3_bucket_name):
    from swag_client.swag import get_by_aws_account_number

    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name,
        'swag.schema_version': 1
    }

    swagv1 = SWAGManager(**parse_swag_config_options(swag_opts))

    account = {
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
        ]
    }

    swagv1.create(account)

    # Test getting account # 012345678910
    account = get_by_aws_account_number('012345678910', s3_bucket_name)
    assert account['name'] == 'testaccount'

    # Test by getting account that does not exist:
    assert not get_by_aws_account_number('thisdoesnotexist', s3_bucket_name)

