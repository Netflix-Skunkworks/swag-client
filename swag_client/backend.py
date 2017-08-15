"""
.. module:: swag_client.backend
    :platform: Unix
.. author:: Kevin Glisson (kglisson@netflix.com)
"""
import logging
import pkg_resources

from beaker.cache import cache_regions, cache_region

import jmespath

from swag_client.exceptions import InvalidSWAGBackendError

logger = logging.getLogger(__name__)


def get(name):
    for ep in pkg_resources.iter_entry_points('swag_client.backends'):
        if ep.name == name:
            try:
                return ep.load()
            except Exception:
                import traceback
                logger.error("Failed to load plugin %r:\n%s\n" % (ep.name, traceback.format_exc()))
                raise InvalidSWAGBackendError


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
        return self.backend.create(item)

    def delete(self, item):
        """Delete an item in backend."""
        return self.backend.delete(item)

    def update(self, item):
        """Update an item in backend."""
        return self.backend.update(item)

    @cache_region('swag')
    def get(self, search_filter):
        """Fetch one item from backend."""
        return self.backend.get(search_filter)

    @cache_region('swag')
    def get_all(self, search_filter=None):
        """Fetch all data from backend."""
        return self.backend.get_all(search_filter=search_filter)

    def get_service_name(self, name, search_filter):
        """Fetch account name as referenced by a particular service. """
        service_filter = "services[?name=='{}'].metadata.name".format(name)
        return jmespath.search(service_filter, self.get(search_filter))[0]

    def get_by_name(self, name, alias=None):
        """Fetch all accounts with name specified, optionally include aliases."""
        search_filter = "[?name=='{}']".format(name)

        if alias:
            if self.version == 1:
                search_filter = "accounts[?alias[?contains(@, '{}') == `true`]]".format(name)

            elif self.version == 2:
                search_filter = "[?aliases[?contains(@, '{}') == `true`]]".format(name)

        return self.get_all(search_filter)

