import json
import click
from tabulate import tabulate
from time import sleep


from swag_client.backend import SWAGManager
from swag_client.util import parse_swag_config_options
from swag_client.schemas import v1, v2


def validate_data(data, version=None):
    if version == 1:
        return v1.AccountSchema().load(data)
    else:
        return v2.AccountSchema().load(data)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('data', type=click.Path(exists=True))
@click.option('--bucket-region')
@click.option('--bucket-name')
@click.option('--type')
@click.option('--data-dir')
@click.option('--namespace')
def create(data, bucket_region, bucket_name, type, data_dir, namespace):
    swag_opts = {
        'swag.type': type,
        'swag.data_dir': data_dir,
        'swag.bucket_name': bucket_name,
        'swag.region': bucket_region,
        'swag.namespace': namespace
    }

    # remove none values
    swag_opts = {key: value for (key, value) in swag_opts.items() if value}
    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    data = json.loads(data.read())
    data, errors = validate_data(data)

    if errors:
        click.echo(
            click.style('Validation failed. Errors: {errors}'.format(errors=errors), fg='red')
        )
    else:
        swag.create(data)


@cli.command()
@click.argument('data', type=click.File())
def validate(data, version):
    data = json.loads(data.read())

    if version == 1:
        data = data['accounts']

    for account in data:
        data, errors = validate_data(account)
        if errors:
            click.echo(
                click.style('Validation failed. Errors: {errors}'.format(errors=errors), fg='red')
            )
    else:
        click.echo(
            click.style('Validation successful.', fg='green')
        )


@cli.command()
@click.argument('data', type=click.File())
@click.option('--version', type=click.INT, default=1)
def upgrade(data, version):
    """Converts data to latest schema version"""
    data = json.loads(data.read())
    accounts = []
    if version == 1:
        for account in data['accounts']:
            if validate_data(account, version):
                accounts.append(v2.upgrade(account))

    click.echo(
        json.dumps(accounts)
    )


@cli.command()
@click.argument('data', type=click.File())
@click.option('--version', type=click.INT, default=1)
def bootstrap_dynamodb(data, version):
    """Bootstraps dynamodb from a json file."""
    swag_opts = {
        'swag.type': 'dynamodb',
        'swag.key_type': 'HASH',
        'swag.key_attribute': 'id'
    }

    # remove none values
    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    data = json.loads(data.read())
    if version == 1:
        for account in data['accounts']:
            if validate_data(account, version):
                swag.create(v2.upgrade(account))
                sleep(2)


@cli.command()
@click.option('--bucket-region')
@click.option('--bucket-name')
@click.option('--type')
@click.option('--data-dir')
@click.option('--namespace')
def list(bucket_region, bucket_name, type, data_dir, namespace):
    """Display all accounts tracked by SWAG"""
    swag_opts = {
        'swag.type': type,
        'swag.data_dir': data_dir,
        'swag.bucket_name': bucket_name,
        'swag.region': bucket_region,
        'swag.namespace': namespace
    }

    # remove none values
    swag_opts = {key: value for (key, value) in swag_opts.items() if value}

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    accounts = swag.get_all()
    _table = [[result['name'], result.get('id')] for result in accounts]
    click.echo(
        tabulate(_table, headers=["Account Name", "Account Number"])
    )
