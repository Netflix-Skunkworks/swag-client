"""Contains the revision information for a given SWAG Table"""

revision = 'v2'
down_revision = None


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
                    enabled=account['services'][service].get('enabled', True)
                )
            ]
        )

        if service == 'spinnaker':
            s['metadata'] = {'name': account['services'][service]['name']}

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

    status = []
    if account['type'] == 'aws':
        status = [
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
            },
            {
                'region': 'us-east-2',
                'status': 'in-active'
            },
            {
                'region': 'us-west-1',
                'status': 'in-active'
            },
            {
                'region': 'ca-central-1',
                'status': 'in-active'
            },
            {
                'region': 'ap-south-1',
                'status': 'in-active'
            },
            {
                'region': 'ap-northeast-2',
                'status': 'in-active'
            },
            {
                'region': 'ap-northeast-1',
                'status': 'in-active'
            },
            {
                'region': 'ap-southeast-1',
                'status': 'in-active'
            },
            {
                'region': 'ap-southeast-2',
                'status': 'in-active'
            },
            {
                'region': 'eu-west-2',
                'status': 'in-active'
            },
            {
                'region': 'eu-central-1',
                'status': 'in-active'
            },
            {
                'region': 'sa-east-1',
                'status': 'in-active'
            },
        ]

    return dict(
        id=item_id,
        email=account['metadata'].get('email'),
        name=account['name'],
        contacts=account['owners'],
        provider=account['type'],
        status=status,
        tags=list(set(account['tags'])),
        environment=environ,
        description=account['description'],
        sensitive=account['cmc_required'],
        owner=owner,
        aliases=account['alias'],
        services=services,
        account_status=account['account_status']
    )


def downgrade(account):
    """Transforms data from v2 format to a v1 format"""
    d_account = dict(schema_version=1, metadata={'email': account['email']},
                     tags=list(set([account['environment']] + account.get('tags', []))))

    v1_services = {}
    for service in account.get('services', []):
        if service['name'] == 's3':
            if service['metadata'].get('name'):
                d_account['metadata']['s3_name'] = service['metadata']['name']

        elif service['name'] == 'cloudtrail':
            d_account['metadata']['cloudtrail_index'] = service['metadata']['esIndex']
            d_account['metadata']['cloudtrail_kibana_url'] = service['metadata']['kibanaUrl']

        elif service['name'] == 'bastion':
            d_account['bastion'] = service['metadata']['hostname']

        elif service['name'] == 'titus':
            v1_services['titus'] = {
                'stacks': service['metadata']['stacks'],
                'enabled': service['status'][0]['enabled']
            }

        elif service['name'] == 'spinnaker':
            v1_services['spinnaker'] = {
                'name': service['metadata'].get('name', account["name"]),
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
    d_account['account_status'] = account['account_status']

    return d_account
