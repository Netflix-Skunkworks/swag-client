from deepdiff import DeepDiff
from marshmallow.exceptions import ValidationError
import pytest


def test_upgrade_1_to_2():
    from swag_client.migrations.versions.v2 import upgrade, downgrade

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
            "testing",
            "test"
        ],
        "netflix": True,
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
        },
        "account_status": "ready"
    }

    v2 = upgrade(a)

    v1 = downgrade(v2)
    assert not DeepDiff(v1, a, ignore_order=True)


def test_file_backend_get_all(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v2',
        'swag.cache_expires': 0
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))
    assert len(swag.get_all()) == 2


def test_file_backend_get_service_enabled(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v2',
        'swag.cache_expires': 0
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    enabled = swag.get_service_enabled('myService')
    assert len(enabled) == 1

    enabled = swag.get_service_enabled('myService', region='us-east-1')
    assert len(enabled) == 1

    enabled = swag.get_service_enabled('myService1')
    assert len(enabled) == 0

    enabled = swag.get_service_enabled('myService1', region='us-east-1')
    assert len(enabled) == 0

    enabled = swag.get_service_enabled('myService2', region='us-east-1')
    assert len(enabled) == 1

    enabled = swag.get_service_enabled('myService2')
    assert len(enabled) == 1


def test_file_backend_get_service_enabled_v1(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v1',
        'swag.cache_expires': 0,
        'swag.schema_version': 1
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    enabled = swag.get_service_enabled('myService')
    assert len(enabled) == 1

    enabled = swag.get_service_enabled('myService', region='us-east-1')
    assert len(enabled) == 1

    enabled = swag.get_service_enabled('myService1')
    assert len(enabled) == 1

    enabled = swag.get_service_enabled('myService1', region='us-east-1')
    assert len(enabled) == 1

    enabled = swag.get_service_enabled('myService2', region='us-east-1')
    assert len(enabled) == 0

    enabled = swag.get_service_enabled('myService2')
    assert len(enabled) == 0


def test_file_backend_update(temp_file_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_file': str(temp_file_name),
        'swag.cache_expires': 0
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
        'swag.data_file': str(temp_file_name),
        'swag.cache_expires': 0
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
        'swag.data_file': str(temp_file_name),
        'swag.cache_expires': 0
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
        'swag.namespace': 'valid_accounts_v2',
        'swag.cache_expires': 0
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    assert swag.get("[?id=='012345678910']")


def test_backend_get_by_name(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v2',
        'swag.cache_expires': 0
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    assert swag.get_by_name('testaccount')
    assert not swag.get_by_name('test')
    assert swag.get_by_name('test', alias=True)
    assert swag.get_by_name('testaccount', alias=True)


def test_backend_get_service_name(vector_path):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.data_dir': vector_path,
        'swag.namespace': 'valid_accounts_v2',
        'swag.cache_expires': 0
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))
    assert swag.get_service_name('myService', "[?name=='testaccount']") == 'testaccount'


def test_s3_backend_get_all(s3_bucket_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name,
        'swag.cache_expires': 0
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
        'swag.bucket_name': s3_bucket_name,
        'swag.cache_expires': 0
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
        'swag.bucket_name': s3_bucket_name,
        'swag.cache_expires': 0
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


def test_s3_backend_delete_v1(s3_bucket_name):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name,
        'swag.schema_version': 1,
        'swag.cache_expires': 0
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
        "email": "bob@example.com",
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
        'swag.bucket_name': s3_bucket_name,
        'swag.cache_expires': 0
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
        'swag.bucket_name': s3_bucket_name,
        'swag.cache_expires': 0
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


def test_dynamodb_backend_get(dynamodb_table):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.cache_expires': 0
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


def test_dynamodb_backend_get_all(dynamodb_table):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.cache_expires': 0
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


def test_dynamodb_backend_update(dynamodb_table):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.key_type': 'HASH',
        'swag.key_attribute': 'id',
        'swag.cache_expires': 0
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


def test_dynamodb_backend_delete(dynamodb_table):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.cache_expires': 0
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


def test_dynamodb_backend_create(dynamodb_table):
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.namespace': 'accounts',
        'swag.cache_expires': 0
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
        'swag.schema_version': 1,
        'swag.cache_expires': 0
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
        "email": "joe@example.com",
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


def test_downgrade_spinnaker():
    """Test without any metadata name set -- should default to the account name"""
    from swag_client.migrations.versions.v2 import downgrade
    account_spinnaker = {
        "email": "spinnakertestaccount@test.com",
        "services": [
            {
                "metadata": {},
                "status": [
                    {
                        "region": "all",
                        "notes": [],
                        "enabled": True
                    }
                ],
                "name": "spinnaker"
            }
        ],
        "type": "service",
        "aliases": [],
        "description": "Spinnaker Test for Downgrade",
        "schemaVersion": "2",
        "id": "098765432110",
        "name": "testspinnaker",
        "owner": "netflix",
        "contacts": [
            "test@test.com"
        ],
        "status": [
            {
                "status": "created",
                "region": "all",
                "notes": []
            }
        ],
        "sensitive": False,
        "provider": "aws",
        "tags": [],
        "environment": "test",
        "account_status": "ready"
    }

    v1 = downgrade(account_spinnaker)
    assert v1["services"]["spinnaker"]["name"] == "testspinnaker"

    # With the name set:
    account_spinnaker["services"][0]["metadata"]["name"] = "lolaccountname"
    v1 = downgrade(account_spinnaker)
    assert v1["services"]["spinnaker"]["name"] == "lolaccountname"



def test_get_by_name(s3_bucket_name):
    from swag_client.swag import get_by_name

    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name,
        'swag.schema_version': 1,
        'swag.cache_expires': 0
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
        "email": "joe@example.com",
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
        'swag.schema_version': 1,
        'swag.cache_expires': 0
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
        "email": "bob@example.com",
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


def test_schema_context_validation_type_field():
    """Test schema context validation for type field"""
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.schema_context': {
            'type': ['billing', 'security', 'shared-service', 'service'],
        }
    }
    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    data = {
        "aliases": ["test"],
        "contacts": ["admins@test.net"],
        "description": "This is just a test.",
        "email": "test@example.net",
        "environment": "dev",
        "id": "012345678910",
        "name": "testaccount",
        "owner": "netflix",
        "provider": "aws",
    }

    # Test with invalid account type
    with pytest.raises(ValidationError):
        data['type'] = 'bad_type'
        swag.create(data)

    # Test with a valid account type
    data['type'] = 'billing'
    account = swag.create(data)
    assert account.get('type') == 'billing'


def test_schema_context_validation_environment_field():
    """Test schema context validation for environment field"""
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.schema_context': {
            'environment': ['test', 'prod']
        }
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    data = {
        "aliases": ["test"],
        "contacts": ["admins@test.net"],
        "description": "This is just a test.",
        "email": "test@example.net",
        "id": "012345678910",
        "name": "testaccount",
        "owner": "netflix",
        "provider": "aws",
    }

    # Test with invalid environment
    with pytest.raises(ValidationError):
        data['environment'] = 'bad_environment'
        swag.create(data)

    # Test with a valid environment
    data['environment'] = 'test'
    account = swag.create(data)
    assert account.get('environment') == 'test'

def test_schema_context_validation_owner_field():
    """Test schema context validation for owner field"""
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.schema_context': {
            'owner': ['netflix', 'dvd', 'aws', 'third-party']
        }
    }
    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    data = {
        "aliases": ["test"],
        "contacts": ["admins@test.net"],
        "description": "This is just a test.",
        "email": "test@example.net",
        "id": "012345678910",
        "name": "testaccount",
        "environment": "test",
        "provider": "aws",
    }

    # Test with invalid owner
    with pytest.raises(ValidationError):
        data['owner'] = 'bad_owner'
        swag.create(data)

    # Test with a valid owner
    data['owner'] = 'netflix'
    account = swag.create(data)
    assert account.get('owner') == 'netflix'

def test_schema_validation_account_status_field(s3_bucket_name):
    """Test schema context validation for owner field"""
    from swag_client.backend import SWAGManager
    from swag_client.util import parse_swag_config_options

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': s3_bucket_name,
        'swag.schema_version': 2,
        'swag.cache_expires': 0
    }
    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    data = {
        "aliases": ["test"],
        "contacts": ["admins@test.net"],
        "description": "This is just a test.",
        "email": "test@example.net",
        "id": "012345678910",
        "name": "testaccount",
        "environment": "test",
        "provider": "aws",
        "status": [
            {
                "region": "us-west-2",
                "status": "created",
                "notes": []
            }
        ],
        "account_status": "deleted"
    }

    # Test with invalid account_status
    with pytest.raises(ValidationError):
        swag.create(data)

    # Test with a valid account_status
    data['account_status'] = 'created'
    account = swag.create(data)
    assert account.get('account_status') == 'created'
