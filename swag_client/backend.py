"""
.. module:: swag_client.backend
    :platform: Unix
.. author:: Kevin Glisson (kglisson@netflix.com)
"""
import logging
import pkg_resources

import jmespath

from swag_client.schemas import v1, v2
from swag_client.util import parse_swag_config_options
from swag_client.exceptions import InvalidSWAGDataException

logger = logging.getLogger(__name__)


def validate(item, namespace='accounts', version=2, context=None):
    """Validate item against version schema.
    
    Args:
        item: data object
        namespace: backend namespace
        version: schema version
        context: schema context object
    """
    if namespace == 'accounts':
        if version == 2:
            schema = v2.AccountSchema(strict=True, context=context)
            return schema.load(item).data
        elif version == 1:
            return v1.AccountSchema(strict=True).load(item).data
        raise InvalidSWAGDataException('Schema version is not supported. Version: {}'.format(version))
    raise InvalidSWAGDataException('Namespace not supported. Namespace: {}'.format(namespace))


def one(items):
    """Fetches one item from a list. Throws exception if there are multiple items."""
    if items:
        if len(items) > 1:
            raise InvalidSWAGDataException('Attempted to fetch one item, but multiple items found.')
        return items[0]


def get(name):
    for ep in pkg_resources.iter_entry_points('swag_client.backends'):
        if ep.name == name:
            return ep.load()


class SWAGManager(object):
    """Manages swag backends."""
    def __init__(self, *args, **kwargs):
        if kwargs:
            self.configure(*args, **kwargs)

    def configure(self, *args, **kwargs):
        """Configures a SWAG manager. Overrides existing configuration."""

        self.version = kwargs['schema_version']
        self.namespace = kwargs['namespace']
        self.backend = get(kwargs['type'])(*args, **kwargs)
        self.context = kwargs.pop('schema_context', {})

    def create(self, item, dry_run=None):
        """Create a new item in backend."""
        return self.backend.create(validate(item, version=self.version, context=self.context), dry_run=dry_run)

    def delete(self, item, dry_run=None):
        """Delete an item in backend."""
        return self.backend.delete(item, dry_run=dry_run)

    def update(self, item, dry_run=None):
        """Update an item in backend."""
        return self.backend.update(validate(item, version=self.version, context=self.context), dry_run=dry_run)

    def get(self, search_filter):
        """Fetch one item from backend."""
        return one(self.get_all(search_filter))

    def get_all(self, search_filter=None):
        """Fetch all data from backend."""
        items = self.backend.get_all()

        if not items:
            if self.version == 1:
                return {self.namespace: []}
            return []

        if search_filter:
            items = jmespath.search(search_filter, items)

        return items

    def health_check(self):
        """Performs a health check specific to backend technology."""
        return self.backend.health_check()

    def get_service_enabled(self, name, accounts_list=None, search_filter=None, region=None):
        """Get a list of accounts where a service has been enabled."""
        if not accounts_list:
            accounts = self.get_all(search_filter=search_filter)
        else:
            accounts = accounts_list

        if self.version == 1:
            accounts = accounts['accounts']

        enabled = []
        for account in accounts:
            if self.version == 1:
                account_filter = "accounts[?id=='{id}']".format(id=account['id'])
            else:
                account_filter = "[?id=='{id}']".format(id=account['id'])

            service = self.get_service(name, search_filter=account_filter)

            if self.version == 1:
                if service:
                    service = service['enabled']  # no region information available in v1
            else:
                if not region:
                    service_filter = "status[?enabled]"
                else:
                    service_filter = "status[?(region=='{region}' || region=='all') && enabled]".format(region=region)

                service = jmespath.search(service_filter, service)

            if service:
                enabled.append(account)

        return enabled

    def get_service(self, name, search_filter):
        """Fetch service metadata."""
        if self.version == 1:
            service_filter = "service.{name}".format(name=name)
            return jmespath.search(service_filter, self.get(search_filter))
        else:
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
                search_filter = "accounts[?name=='{name}' || contains(alias, '{name}')]".format(name=name)

            elif self.version == 2:
                search_filter = "[?name=='{name}' || contains(aliases, '{name}')]".format(name=name)

        return self.get_all(search_filter)
