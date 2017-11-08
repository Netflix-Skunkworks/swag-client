"""
.. module:: swag_client.backend
    :platform: Unix
.. author:: Kevin Glisson (kglisson@netflix.com)
"""
import logging
import pkg_resources

import jmespath
from beaker.cache import cache_regions, cache_region

from swag_client.schemas import v1, v2
from swag_client.exceptions import InvalidSWAGBackendError, InvalidSWAGDataException

logger = logging.getLogger(__name__)


def validate(item, namespace='accounts', version=2):
    """Validate item against version schema."""
    if namespace == 'accounts':
        if version == 2:
            return v2.AccountSchema(strict=True).load(item).data
        elif version == 1:
            return v1.AccountSchema(strict=True).load(item).data
        raise InvalidSWAGDataException('Schema version is not supported. Version: {}'.format(version))
    raise InvalidSWAGDataException('Namespace not supported. Namespace: {}'.format(namespace))


def one(items):
    """Fetches one item from a list. Throws exception if there are multiple items."""
    if items:
        if len(items) > 1:
            raise InvalidSWAGBackendError('Attempted to fetch one item, but multiple items found.')

        return items[0]


def get(name):
    for ep in pkg_resources.iter_entry_points('swag_client.backends'):
        if ep.name == name:
            return ep.load()


class SWAGManager(object):
    """Manages swag backends."""
    def __init__(self, *args, **kwargs):
        self.version = kwargs['schema_version']
        self.backend = get(kwargs['type'])(*args, **kwargs)
        cache_regions.update({
            'swag': {
                'expire': kwargs['cache_expires'],
                'type': 'memory'
            }
        })

    def create(self, item):
        """Create a new item in backend."""
        return self.backend.create(validate(item, version=self.version))

    def delete(self, item):
        """Delete an item in backend."""
        return self.backend.delete(item)

    def update(self, item):
        """Update an item in backend."""
        return self.backend.update(validate(item, version=self.version))

    @cache_region('swag')
    def get(self, search_filter):
        """Fetch one item from backend."""
        return self.backend.get(search_filter)

    @cache_region('swag')
    def get_all(self, search_filter=None):
        """Fetch all data from backend."""
        return self.backend.get_all(search_filter=search_filter)

    def get_service_enabled(self, service_name, accounts_list=None):
        if not accounts_list:
            accounts_list = self.backend.get_all().get('accounts', [])

        service_enabled_accounts = []

        for account in accounts_list:
            for service in account.get('services', []):
                # The part we need to get to is a little buried.  Basically, we need to scan the list of services for
                # a dictionary where the name key matches, then we have to scan the status key, which is a list, and
                # then look for a dictionary where the enabled key is set to True
                if(service['name'] == service_name and
                   len(list(filter(lambda status: status['enabled'], service.get('status', []))))):
                    service_enabled_accounts.append(account)
                    break
        return service_enabled_accounts

    def get_service(self, name, search_filter):
        """Fetch service metadata."""
        service_filter = "services[?name=='{}']".format(name)
        return one(jmespath.search(service_filter, self.get(search_filter)))

    def get_service_name(self, name, search_filter):
        """Fetch account name as referenced by a particular service. """
        service_filter = "services[?name=='{}'].metadata.name".format(name)
        return one(jmespath.search(service_filter, self.get(search_filter)))

    def get_by_name(self, name, alias=None):
        """Fetch all accounts with name specified, optionally include aliases."""
        search_filter = "[?name=='{}']".format(name)

        if alias:
            if self.version == 1:
                search_filter = "accounts[?name=='{name}' || alias[?contains(@, '{name}') == `true`]]".format(name=name)

            elif self.version == 2:
                search_filter = "[?name=='{name}' || aliases[?contains(@, '{name}') == `true`]]".format(name=name)

        return self.get_all(search_filter)
