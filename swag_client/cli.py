import logging
import os
import time
import json
import click
import click_log
from tabulate import tabulate

from swag_client.backend import SWAGManager
from swag_client.__about__ import __version__
from swag_client.migrations import run_migration
from swag_client.util import parse_swag_config_options
from swag_client.exceptions import InvalidSWAGDataException


log = logging.getLogger('swag_client')
click_log.basic_config(log)


class CommaList(click.ParamType):
    name = 'commalist'

    def convert(self, value, param, ctx):
        return value.split(',')


def create_swag_from_ctx(ctx):
    """Creates SWAG client from the current context."""
    swag_opts = {}
    if ctx.type == 'file':
        swag_opts = {
            'swag.type': 'file',
            'swag.data_dir': ctx.data_dir,
            'swag.data_file': ctx.data_file
        }
    elif ctx.type == 's3':
        swag_opts = {
            'swag.type': 's3',
            'swag.bucket_name': ctx.bucket_name,
            'swag.data_file': ctx.data_file,
            'swag.region': ctx.region
        }
    elif ctx.type == 'dynamodb':
        swag_opts = {
            'swag.type': 'dynamodb',
            'swag.region': ctx.region
        }
    return SWAGManager(**parse_swag_config_options(swag_opts))


class AppContext(object):
    def __init__(self):
        self.namespace = None
        self.region = None
        self.type = None
        self.data_dir = None
        self.data_file = None
        self.bucket_name = None
        self.dry_run = None


pass_context = click.make_pass_decorator(AppContext, ensure=True)


@click.group()
@click.option('--namespace', default='accounts')
@click.option('--dry-run', type=bool, default=False, is_flag=True, help='Run command without persisting anything.')
@click_log.simple_verbosity_option(log)
@click.version_option(version=__version__)
@pass_context
def cli(ctx, namespace, dry_run):
    if not ctx.namespace:
        ctx.namespace = namespace

    if not ctx.dry_run:
        ctx.dry_run = dry_run


@cli.group()
@click.option('--region', default='us-east-1', help='Region the table is located in.')
@pass_context
def dynamodb(ctx, region):
    if not ctx.region:
        ctx.region = region

    ctx.type = 'dynamodb'


@cli.group()
@click.option('--data-dir', help='Directory to store data.', default=os.getcwd())
@click.option('--data-file')
@pass_context
def file(ctx, data_dir, data_file):
    """Use the File SWAG Backend"""
    if not ctx.file:
        ctx.data_file = data_file

    if not ctx.data_dir:
        ctx.data_dir = data_dir

    ctx.type = 'file'


@cli.group()
@click.option('--bucket-name', help='Name of the bucket you wish to operate on.')
@click.option('--data-file', help='Key name of the file to operate on.')
@click.option('--region', default='us-east-1', help='Region the bucket is located in.')
@pass_context
def s3(ctx, bucket_name, data_file, region):
    """Use the S3 SWAG backend."""
    if not ctx.data_file:
        ctx.data_file = data_file

    if not ctx.bucket_name:
        ctx.bucket_name = bucket_name

    if not ctx.region:
        ctx.region = region

    ctx.type = 's3'


@cli.command()
@pass_context
def list(ctx):
    """List SWAG account info."""
    if ctx.namespace != 'accounts':
        click.echo(
            click.style('Only account data is available for listing.', fg='red')
        )
        return

    swag = create_swag_from_ctx(ctx)
    accounts = swag.get_all()
    _table = [[result['name'], result.get('id')] for result in accounts]
    click.echo(
        tabulate(_table, headers=["Account Name", "Account Number"])
    )


@cli.command()
@click.option('--name', help='Name of the service to list.')
@pass_context
def list_service(ctx, name):
    """Retrieve accounts pertaining to named service."""
    swag = create_swag_from_ctx(ctx)
    accounts = swag.get_service_enabled(name)

    _table = [[result['name'], result.get('id')] for result in accounts]
    click.echo(
        tabulate(_table, headers=["Account Name", "Account Number"])
    )


@cli.command()
@click.option('--start-version', default=1, help='Starting version.')
@click.option('--end-version', default=2, help='Ending version.')
@pass_context
def migrate(ctx, start_version, end_version):
    """Transition from one SWAG schema to another."""
    if ctx.type == 'file':
        if ctx.data_file:
            file_path = ctx.data_file
        else:
            file_path = os.path.join(ctx.data_file, ctx.namespace + '.json')

        # todo make this more like alemebic and determine/load versions automatically
        with open(file_path, 'r') as f:
            data = json.loads(f.read())

        data = run_migration(data, start_version, end_version)
        with open(file_path, 'w') as f:
            f.write(json.dumps(data))


@cli.command()
@pass_context
def propagate(ctx):
    """Transfers SWAG data from one backend to another"""
    data = []
    if ctx.type == 'file':
        if ctx.data_file:
            file_path = ctx.data_file
        else:
            file_path = os.path.join(ctx.data_dir, ctx.namespace + '.json')

        with open(file_path, 'r') as f:
            data = json.loads(f.read())

    swag_opts = {
        'swag.type': 'dynamodb'
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))

    for item in data:
        time.sleep(2)
        swag.create(item, dry_run=ctx.dry_run)


@cli.command()
@pass_context
def create(ctx):
    """Create a new SWAG item."""
    pass


@cli.command()
@pass_context
@click.argument('data', type=click.File())
def update(ctx, data):
    """Updates a given record."""
    swag = create_swag_from_ctx(ctx)
    data = json.loads(data.read())

    for account in data:
        swag.update(account, dry_run=ctx.dry_run)


@cli.command()
@pass_context
@click.argument('name')
@click.option('--path', type=str, default='', help='JMESPath string to filter accounts to be targeted. Default is all accounts.')
@click.option('--regions', type=CommaList(), default='all',
              help='AWS regions that should be configured. These are comma delimited (e.g. us-east-1, us-west-2, eu-west-1). Default: all')
@click.option('--disabled', type=bool, default=False, is_flag=True, help='Service should be marked as enabled.')
def deploy_service(ctx, path, name, regions, disabled):
    """Deploys a new service JSON to multiple accounts. NAME is the service name you wish to deploy."""
    enabled = False if disabled else True

    swag = create_swag_from_ctx(ctx)
    accounts = swag.get_all(search_filter=path)
    log.debug('Searching for accounts. Found: {} JMESPath: `{}`'.format(len(accounts), path))
    for a in accounts:
        try:
            if not swag.get_service(name, search_filter="[?id=='{id}']".format(id=a['id'])):
                log.info('Found an account to update. AccountName: {name} AccountNumber: {number}'.format(name=a['name'], number=a['id']))
                status = []
                for region in regions:
                    status.append(
                        {
                            'enabled': enabled,
                            'region': region

                         }
                    )
                a['services'].append(
                    {
                        'name': name,
                        'status': status
                     }
                )

                swag.update(a, dry_run=ctx.dry_run)
        except InvalidSWAGDataException as e:
            log.warning('Found a data quality issue. AccountName: {name} AccountNumber: {number}'.format(name=a['name'], number=a['id']))

    log.info('Service has been deployed to all matching accounts.')


@cli.command()
@pass_context
@click.argument('data', type=click.File())
def seed_aws_data(ctx, data):
    """Seeds SWAG from a list of known AWS accounts."""
    swag = create_swag_from_ctx(ctx)
    for k, v in json.loads(data.read()).items():
        for account in v['accounts']:
            data = {
                    'description': 'This is an AWS owned account used for {}'.format(k),
                    'id': account['account_id'],
                    'contacts': [],
                    'owner': 'aws',
                    'provider': 'aws',
                    'sensitive': False,
                    'email': 'support@amazon.com',
                    'name': k + '-' + account['region']
                }

            click.echo(click.style(
                'Seeded Account. AccountName: {}'.format(data['name']), fg='green')
            )

            swag.create(data, dry_run=ctx.dry_run)


# todo perhaps there is a better way of dynamically adding subcommands?
file.add_command(list)
file.add_command(migrate)
file.add_command(propagate)
file.add_command(create)
file.add_command(seed_aws_data)
file.add_command(update)
file.add_command(deploy_service)
file.add_command(list_service)
dynamodb.add_command(list)
dynamodb.add_command(create)
dynamodb.add_command(update)
dynamodb.add_command(seed_aws_data)
dynamodb.add_command(deploy_service)
dynamodb.add_command(list_service)
s3.add_command(list)
s3.add_command(create)
s3.add_command(update)
s3.add_command(seed_aws_data)
s3.add_command(deploy_service)
s3.add_command(list_service)


