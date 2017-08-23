import logging

import boto3
import jmespath

from swag_client.backend import SWAGManager

logger = logging.getLogger(__file__)


class DynamoDBSWAGManager(SWAGManager):
    def __init__(self, namespace, **kwargs):
        """Create a DynamoDb based SWAG backend."""
        self.namespace = namespace
        resource = boto3.resource('dynamodb', region_name=kwargs['region'])
        self.table = resource.Table(namespace)

    def get(self, search_filter):
        """Fetch one item from file. Applying given filter, raises exception if more than one item found."""
        logger.debug('Fetching items. Filter: {filter}. Table: {namespace}'.format(
            filter=search_filter,
            namespace=self.namespace
        ))

        items = self.table.scan()['Items']
        results = jmespath.search(search_filter, items)

        if len(results) > 1:
            raise Exception('Found more than one result for get!')

        elif len(results) == 1:
            return results[0]

    def create(self, item):
        """Creates a new item in file."""
        logger.debug('Creating new item. Item: {item} Table: {namespace}'.format(
            item=item,
            namespace=self.namespace
        ))

        self.table.put_item(Item=item)

        return item

    def delete(self, item):
        """Deletes item in file."""
        logger.debug('Deleting item. Item: {item} Table: {namespace}'.format(
            item=item,
            namespace=self.namespace
        ))

        self.table.delete_item(Key={'id': item['id']})

    def update(self, item):
        """Updates item info in file."""
        logger.debug('Updating item. Item: {item} Table: {namespace}'.format(
            item=item,
            namespace=self.namespace
        ))
        self.table.put_item(Item=item)
        return item

    def get_all(self, search_filter=None):
        """Gets all items in file."""
        logger.debug('Fetching items. Filter: {filter}. Table: {namespace}'.format(
            filter=search_filter,
            namespace=self.namespace
        ))

        items = self.table.scan()['Items']

        if search_filter:
            return jmespath.search(search_filter, items)

        return items
