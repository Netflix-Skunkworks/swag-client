import os
import sys
import json
import logging
from io import open

from dogpile.cache import make_region

from swag_client.backend import SWAGManager
from swag_client.util import append_item, remove_item

logger = logging.getLogger(__name__)

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


file_region = make_region()


def load_file(data_file):
    """Tries to load JSON from data file."""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.loads(f.read())

    except JSONDecodeError as e:
        return []


def save_file(data_file, data, dry_run=None):
    """Writes JSON data to data file."""
    if dry_run:
        return

    with open(data_file, 'w', encoding='utf-8') as f:
        if sys.version_info > (3, 0):
            f.write(json.dumps(data))
        else:
            f.write(json.dumps(data).decode('utf-8'))


class FileSWAGManager(SWAGManager):
    def __init__(self, namespace, **kwargs):
        """Create a file based SWAG backend."""
        self.namespace = namespace
        self.version = kwargs['schema_version']

        if not file_region.is_configured:
            file_region.configure(
                'dogpile.cache.memory',
                expiration_time=kwargs['cache_expires']
            )

        if not kwargs.get('data_file'):
            self.data_file = os.path.join(kwargs['data_dir'], self.namespace + '.json')
        else:
            self.data_file = kwargs['data_file']

        if not os.path.isfile(self.data_file):
            logger.warning(
                'Backend file does not exist, creating... Path: {data_file}'.format(data_file=self.data_file)
            )

            save_file(self.data_file, [])

    def create(self, item, dry_run=None):
        """Creates a new item in file."""
        logger.debug('Creating new item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))

        items = load_file(self.data_file)
        items = append_item(self.namespace, self.version, item, items)
        save_file(self.data_file, items, dry_run=dry_run)

        return item

    def delete(self, item, dry_run=None):
        """Deletes item in file."""
        logger.debug('Deleting item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))

        items = load_file(self.data_file)
        items = remove_item(self.namespace, self.version, item, items)
        save_file(self.data_file, items, dry_run=dry_run)

        return item

    def update(self, item, dry_run=None):
        """Updates item info in file."""
        logger.debug('Updating item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))
        self.delete(item, dry_run=dry_run)
        return self.create(item, dry_run=dry_run)

    @file_region.cache_on_arguments()
    def get_all(self):
        """Gets all items in file."""
        logger.debug('Fetching items. Path: {data_file}'.format(
            data_file=self.data_file
        ))

        return load_file(self.data_file)


    def health_check(self):
        """Checks to make sure the file is there."""
        logger.debug('Health Check on file for: {namespace}'.format(
            namespace=self.namespace
        ))

        return os.path.isfile(self.data_file)
