from datetime import datetime
from marshmallow import Schema, fields
from marshmallow.validate import OneOf

PROVIDERS = ['aws', 'gcp', 'azure']
ACCOUNT_TYPES = ['billing', 'security', 'shared-service', 'service']
ACCOUNT_STATUSES = ['created', 'in-progress', 'ready', 'deprecated', 'deleted', 'in-active']
ACCOUNT_ENVIRONMENTS = ['test', 'prod']
ACCOUNT_OWNERS = ['netflix', 'dvd', 'aws', 'third-party']


class NoteSchema(Schema):
    date = fields.Date(missing=datetime.utcnow())
    text = fields.Str(required=True)


class AccountStatusSchema(Schema):
    region = fields.Str(required=True)
    status = fields.Str(validate=OneOf(ACCOUNT_STATUSES), missing='created')
    notes = fields.Nested(NoteSchema, many=True)


class ServiceStatusSchema(Schema):
    region = fields.Str(required=True)
    enabled = fields.Boolean(missing=False)
    notes = fields.Nested(NoteSchema, many=True)


class ServiceSchema(Schema):
    name = fields.Str(required=True)
    status = fields.Nested(ServiceStatusSchema, many=True)
    groups = fields.List(fields.Str())
    metadata = fields.Dict()


class AccountSchema(Schema):
    schemaVersion = fields.Int(missing=2)
    id = fields.Str(required=True)
    name = fields.Str(required=True)
    contacts = fields.List(fields.Email(), required=True)
    provider = fields.Str(validate=OneOf(PROVIDERS), missing='aws')
    type = fields.Str(validate=OneOf(ACCOUNT_TYPES), missing='service')
    tags = fields.List(fields.Str())
    status = fields.Nested(AccountStatusSchema, many=True)
    email = fields.Email()
    environment = fields.Str(validate=OneOf(ACCOUNT_ENVIRONMENTS), missing='test')
    services = fields.Nested(ServiceSchema, many=True)
    sensitive = fields.Bool(missing=False)
    description = fields.Str(required=True)
    owner = fields.Str(validate=OneOf(ACCOUNT_OWNERS), required=True)
    aliases = fields.List(fields.Str())


def upgrade(account):
    """Transforms data from a v1 format to a v2 format"""
    environ = 'test'
    if 'prod' in account['tags']:
        environ = 'prod'

    owner = 'netflix'
    if not account['ours']:
        owner = 'third-party'

    services = []
    if account['metadata'].get('s3_name'):
        services.append(
            dict(
                name='s3',
                metadata=dict(
                    name=account['metadata']['s3_name']
                ),
                status=[
                    dict(
                        region='all',
                        enabled=True
                    )
                ]
            )
        )

    if account['metadata'].get('cloudtrail_index'):
        services.append(
            dict(
                name='cloudtrail',
                metadata=dict(
                    esIndex=account['metadata']['cloudtrail_index'],
                    kibanaUrl=account['metadata']['cloudtrail_kibana_url']
                ),
                status=[
                    dict(
                        region='all',
                        enabled=True
                    )
                ]
            )
        )

    if account.get('bastion'):
        services.append(
            dict(
                name='bastion',
                metadata=dict(
                    hostname=account['bastion']
                ),
                status=[
                    dict(
                        region='all',
                        enabled=True
                    )
                ]
            )
        )

    for service in account['services'].keys():
        s = dict(
            name=service,
            status=[
                dict(
                    region='all',
                    enabled=account['services'][service]['enabled']
                )
            ]
        )

        if service == 'spinnaker':
            s['metadata'] = {'accountName': account['services'][service]['name']}

        if service == 'lazyfalcon':
            if account['services'][service].get('owner'):
                s['metadata'] = {'owner': account['services'][service]['owner']}

        if service == 'titus':
            s['metadata'] = {'stacks': account['services'][service]['stacks']}

        services.append(s)

    if account['metadata'].get('project_id'):
        item_id = account['metadata']['project_id']
    elif account['metadata'].get('account_number'):
        item_id = account['metadata']['account_number']
    else:
        raise Exception('No id found, are you sure this is in v1 swag format.')

    return dict(
            id=item_id,
            email=account['metadata'].get('email'),
            name=account['name'],
            contacts=account['owners'],
            provider=account['type'],
            status=[
                {
                    'region': 'us-east-1',
                    'status': 'ready'
                },
                {
                    'region': 'us-west-2',
                    'status': 'ready'
                },
                {
                    'region': 'eu-west-1',
                    'status': 'ready'
                }
            ],
            tags=list(set(account['tags'])),
            environment=environ,
            description=account['description'],
            sensitive=account['cmc_required'],
            owner=owner,
            aliases=account['alias'],
            services=services
        )


def downgrade(account):
    """Transforms data from v2 format to a v1 format"""
    d_account = dict(metadata={}, tags=list(set([account['environment']] + account.get('tags', []))))

    v1_services = {}
    for service in account.get('services', []):
        if service['name'] == 's3':
            d_account['metadata']['s3_name'] = service['metadata']['name']

        elif service['name'] == 'cloudtrail':
            d_account['metadata']['cloudtrail_index'] = service['metadata']['esIndex']
            d_account['metadata']['cloudtrail_kibana_url'] = service['metadata']['kibanaUrl']

        elif service['name'] == 'bastion':
            d_account['bastion'] = service['metadata']['hostname']

        elif service['name'] == 'spinnaker':
            v1_services['spinnaker'] = {
                'name': service['metadata']['accountName'],
                'enabled': service['status'][0]['enabled']
            }

        elif service['name'] == 'awwwdit':
            v1_services['awwwdit'] = {
                'enabled': service['status'][0]['enabled']
            }

        elif service['name'] == 'security_monkey':
            v1_services['security_monkey'] = {
                'enabled': service['status'][0]['enabled']
            }

        elif service['name'] == 'poseidon':
            v1_services['poseidon'] = {
                'enabled': service['status'][0]['enabled']
            }

        elif service['name'] == 'rolliepollie':
            v1_services['rolliepollie'] = {
                'enabled': service['status'][0]['enabled']
            }

        elif service['name'] == 'lazyfalcon':
            owner = None

            if service.get('metadata'):
                if service['metadata'].get('owner'):
                    owner = service['metadata']['owner']

            v1_services['lazyfalcon'] = {
                'enabled': service['status'][0]['enabled'],
                'owner': owner
            }

    if account['provider'] == 'aws':
        d_account['metadata']['account_number'] = account['id']

    elif account['provider'] == 'gcp':
        d_account['metadata']['project_id'] = account['id']

    d_account['id'] = account['provider'] + '-' + account['id']
    d_account['cmc_required'] = account['sensitive']
    d_account['name'] = account['name']
    d_account['alias'] = account['aliases']
    d_account['description'] = account['description']
    d_account['owners'] = account['contacts']
    d_account['type'] = account['provider']
    d_account['ours'] = True if account['owner'] == 'netflix' else False
    d_account['netflix'] = True if account['owner'] == 'netflix' else False
    d_account['services'] = v1_services

    return d_account
