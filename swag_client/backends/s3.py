import sys
import json
import logging

import boto3
import jmespath
from botocore.exceptions import ClientError

from swag_client.backend import SWAGManager

logger = logging.getLogger(__name__)

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


def load_file(client, bucket, data_file):
    """Tries to load JSON data from S3."""
    logger.debug('Loading item from s3. Bucket: {bucket} Key: {key}'.format(
        bucket=bucket,
        key=data_file
    ))
    try:
        data = client.get_object(Bucket=bucket, Key=data_file)['Body'].read()

        if sys.version_info > (3,):
            data = data.decode('utf-8')

        return json.loads(data)
    except JSONDecodeError as e:
        return
    except ClientError as e:
        logger.exception(e)
        return


def save_file(client, bucket, data_file, items):
    """Tries to write JSON data to data file in S3."""
    logger.debug('Writing {number_items} items to s3. Bucket: {bucket} Key: {key}'.format(
        number_items=len(items),
        bucket=bucket,
        key=data_file
    ))
    return client.put_object(Bucket=bucket, Key=data_file, Body=json.dumps(items), ContentType='application/json', CacheControl='no-cache, no-store, must-revalidate')


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

    def get(self, search_filter):
        """Fetch one item from file. Applying given filter, raises exception if more than one item found."""
        logger.debug('Fetching items. Filter: {filter}. Path: {data_file}'.format(
            filter=search_filter,
            data_file=self.data_file
        ))

        items = load_file(self.client, self.bucket_name, self.data_file)
        results = jmespath.search(search_filter, items)

        if results:
            if len(results) > 1:
                raise Exception('Found more than one result for get!')

            elif len(results) == 1:
                return results[0]
        return results

    def create(self, item):
        """Creates a new item in file."""
        logger.debug('Creating new item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))

        items = self.get_all()
        if self.version == 1:
            items[self.namespace].append(item)
        else:
            items.append(item)

        save_file(self.client, self.bucket_name, self.data_file, items)
        return item

    def delete(self, item):
        """Deletes item in file."""
        logger.debug('Deleting item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))

        if self.version == 1:
            # TODO only supports aws providers
            items = self.get_all("{namespace}[?id!='{id}']".format(
                id=item['id'],
                namespace=self.namespace
            ))
        else:
            items = self.get_all("[?id!='{id}']".format(id=item['id']))

        save_file(self.client, self.bucket_name, self.data_file, items)

    def update(self, item):
        """Updates item info in file."""
        logger.debug('Updating item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))
        self.delete(item)
        return self.create(item)

    def get_all(self, search_filter=None):
        """Gets all items in file."""
        logger.debug('Fetching items. Filter: {filter}. Path: {data_file}'.format(
            filter=search_filter,
            data_file=self.data_file
        ))

        items = load_file(self.client, self.bucket_name, self.data_file)

        # default values
        if not items:
            if self.version == 1:
                return {self.namespace: []}
            return []

        # filter values
        if search_filter:
            items = jmespath.search(search_filter, items)
            if self.version == 1:
                return {self.namespace: items}
            return items

        # return raw values
        return items
