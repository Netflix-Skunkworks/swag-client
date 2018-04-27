import os
import warnings
import jmespath

from marshmallow import Schema, fields
from marshmallow.validate import OneOf


class OptionsSchema(Schema):
    type = fields.String(missing='file', validate=OneOf(['file', 's3', 'dynamodb']))
    namespace = fields.String(required=True, missing='accounts')
    schema_version = fields.Integer(missing=2)  # default version to return data as
    cache_expires = fields.Integer(missing=60)
    schema_context = fields.Dict(missing={})


class FileOptionsSchema(OptionsSchema):
    """Option schema for the file backend."""
    data_dir = fields.String(missing=os.getcwd())
    data_file = fields.String()


class S3OptionsSchema(OptionsSchema):
    """Option schema for the S3 backend."""
    bucket_name = fields.String(required=True)
    data_file = fields.String()
    region = fields.String(missing='us-east-1', validate=OneOf(['us-east-1', 'us-west-2', 'eu-west-1']))


class DynamoDBOptionsSchema(OptionsSchema):
    """Option schema for the DynamoDB backend."""
    key_attribute = fields.String(missing='id')
    key_type = fields.String(missing='HASH')
    read_units = fields.Integer(missing=1)
    write_units = fields.Integer(missing=1)
    region = fields.String(missing='us-east-1', validate=OneOf(['us-east-1', 'us-west-2', 'eu-west-1']))


def parse_swag_config_options(config):
    """Ensures that options passed to the backend are valid."""
    options = {}
    for key, val in config.items():
        if key.startswith('swag.backend.'):
            options[key[12:]] = val
        if key.startswith('swag.'):
            options[key[5:]] = val

    if options.get('type') == 's3':
        return S3OptionsSchema(strict=True).load(options).data
    elif options.get('type') == 'dynamodb':
        return DynamoDBOptionsSchema(strict=True).load(options).data
    else:
        return FileOptionsSchema(strict=True).load(options).data


def deprecated(message):
    """Deprecated function decorator."""
    def wrapper(fn):
        def deprecated_method(*args, **kargs):
            warnings.warn(message, DeprecationWarning, 2)
            return fn(*args, **kargs)
        # TODO: use decorator ?  functools.wrapper ?
        deprecated_method.__name__ = fn.__name__
        deprecated_method.__doc__ = "%s\n\n%s" % (message, fn.__doc__)
        return deprecated_method
    return wrapper


def append_item(namespace, version, item, items):
    if version == 1:
        if items:
            items[namespace].append(item)
        else:
            items = {namespace: [item]}

    else:
        if items:
            items.append(item)
        else:
            items = [item]

    return items


def remove_item(namespace, version, item, items):
    if version == 1:
        # NOTE only supports aws providers
        path = "{namespace}[?id!='{id}']".format(id=item['id'], namespace=namespace)
        return jmespath.search(path, items)
    else:
        return jmespath.search("[?id!='{id}']".format(id=item['id']), items)


def is_sub_dict(sub_dict, dictionary):
    """Legacy filter for determining if a given dict is present."""
    for key in sub_dict.keys():
        if key not in dictionary:
            return False
        if (type(sub_dict[key]) is not dict) and (sub_dict[key] != dictionary[key]):
            return False
        if (type(sub_dict[key]) is dict) and (not is_sub_dict(sub_dict[key], dictionary[key])):
            return False
    return True
