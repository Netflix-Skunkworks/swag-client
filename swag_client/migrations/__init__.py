from swag_client.migrations.versions import v2


def run_migration(data, version_start, version_end):
    """Runs migration against a data set."""
    items = []
    if version_start == 1 and version_end == 2:
        for item in data['accounts']:
            items.append(v2.upgrade(item))

    if version_start == 2 and version_end == 1:
        for item in data:
            items.append(v2.downgrade(item))
        items = {'accounts': items}
    return items
