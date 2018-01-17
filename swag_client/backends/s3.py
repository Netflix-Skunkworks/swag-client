import sys
import json
import logging

import boto3
from botocore.exceptions import ClientError
from retrying import retry

from dogpile.cache import make_region

from swag_client.backend import SWAGManager
from swag_client.util import append_item, remove_item

logger = logging.getLogger(__name__)

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


s3_region = make_region()


@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def _get_from_s3(client, bucket, data_file):
    return client.get_object(Bucket=bucket, Key=data_file)['Body'].read()


@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def _put_to_s3(client, bucket, data_file, body):
    return client.put_object(Bucket=bucket, Key=data_file, Body=body, ContentType='application/json',
                             CacheControl='no-cache, no-store, must-revalidate')


def load_file(client, bucket, data_file):
    """Tries to load JSON data from S3."""
    logger.debug('Loading item from s3. Bucket: {bucket} Key: {key}'.format(
        bucket=bucket,
        key=data_file
    ))
    try:
        data = _get_from_s3(client, bucket, data_file)

        if sys.version_info > (3,):
            data = data.decode('utf-8')

        return json.loads(data)
    except JSONDecodeError as e:
        logger.exception(e)
        return
    except ClientError as e:
        logger.exception(e)
        return


def save_file(client, bucket, data_file, items, dry_run=None):
    """Tries to write JSON data to data file in S3."""
    logger.debug('Writing {number_items} items to s3. Bucket: {bucket} Key: {key}'.format(
        number_items=len(items),
        bucket=bucket,
        key=data_file
    ))

    if not dry_run:
        return _put_to_s3(client, bucket, data_file, json.dumps(items))


class S3SWAGManager(SWAGManager):
    def __init__(self, namespace, **kwargs):
        """Create a S3 based SWAG backend."""
        self.namespace = namespace
        self.version = kwargs['schema_version']

        if kwargs.get('data_file'):
            self.data_file = kwargs['data_file']
        else:
            self.data_file = self.namespace + '.json'

        self.bucket_name = kwargs['bucket_name']
        self.client = boto3.client('s3', region_name=kwargs['region'])

        if not s3_region.is_configured:
            s3_region.configure(
                'dogpile.cache.memory',
                expiration_time=kwargs['cache_expires']
            )

    def create(self, item, dry_run=None):
        """Creates a new item in file."""
        logger.debug('Creating new item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))

        items = load_file(self.client, self.bucket_name, self.data_file)
        items = append_item(self.namespace, self.version, item, items)
        save_file(self.client, self.bucket_name, self.data_file, items, dry_run=dry_run)

        return item

    def delete(self, item, dry_run=None):
        """Deletes item in file."""
        logger.debug('Deleting item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))

        items = load_file(self.client, self.bucket_name, self.data_file)
        items = remove_item(self.namespace, self.version, item, items)
        save_file(self.client, self.bucket_name, self.data_file, items, dry_run=dry_run)

    def update(self, item, dry_run=None):
        """Updates item info in file."""
        logger.debug('Updating item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))
        self.delete(item, dry_run=dry_run)
        return self.create(item, dry_run=dry_run)

    @s3_region.cache_on_arguments()
    def get_all(self):
        """Gets all items in file."""
        logger.debug('Fetching items. Path: {data_file}'.format(
            data_file=self.data_file
        ))

        return load_file(self.client, self.bucket_name, self.data_file)

    def health_check(self):
        """Uses head object to make sure the file exists in S3."""
        logger.debug('Health Check on S3 file for: {namespace}'.format(
            namespace=self.namespace
        ))

        try:
            self.client.head_object(Bucket=self.bucket_name, Key=self.data_file)
            return True
        except ClientError as e:
            logger.debug('Error encountered with S3.  Assume unhealthy')
