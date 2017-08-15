import os
import sys
import json
import logging
from io import open

import jmespath

from swag_client.backend import SWAGManager

logger = logging.getLogger(__name__)

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


def load_file(data_file):
    """Tries to load JSON from data file."""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.loads(f.read())

    except JSONDecodeError as e:
        return []


def save_file(data_file, data):
    """Writes JSON data to data file."""
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

        if not kwargs.get('data_file'):
            self.data_file = os.path.join(kwargs['data_dir'], self.namespace + '.json')
        else:
            self.data_file = kwargs['data_file']

        if not os.path.isfile(self.data_file):
            logger.warning(
                'Backend file does not exist, creating... Path: {data_file}'.format(data_file=self.data_file)
            )

            save_file(self.data_file, [])

    def get(self, search_filter):
        """Fetch one item from file. Applying given filter, raises exception if more than one item found."""
        logger.debug('Fetching items. Filter: {filter}. Path: {data_file}'.format(
            filter=search_filter,
            data_file=self.data_file
        ))

        items = load_file(self.data_file)
        results = jmespath.search(search_filter, items)

        if len(results) > 1:
            raise Exception('Found more than one result for get!')

        elif len(results) == 1:
            return results[0]

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

        save_file(self.data_file, items)
        return item

    def delete(self, item):
        """Deletes item in file."""
        logger.debug('Deleting item. Item: {item} Path: {data_file}'.format(
            item=item,
            data_file=self.data_file
        ))

        if self.version == 1:
            # TODO only supports aws providers
            items = self.get_all("{namespace}[?id!='aws-{id}']".format(
                id=item['id'],
                namespace=self.namespace
            ))
        else:
            items = self.get_all("[?id!='{id}']".format(id=item['id']))

        save_file(self.data_file, items)

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

        items = load_file(self.data_file)

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
