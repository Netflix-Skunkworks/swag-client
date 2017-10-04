from datetime import datetime
from marshmallow import Schema, fields
from marshmallow.validate import OneOf

PROVIDERS = ['aws', 'gcp', 'azure']
ACCOUNT_TYPES = ['billing', 'security', 'shared-service', 'service']
ACCOUNT_STATUSES = ['created', 'in-progress', 'ready', 'deprecated', 'deleted', 'in-active']
ACCOUNT_ENVIRONMENTS = ['test', 'prod']
ACCOUNT_OWNERS = ['netflix', 'dvd', 'aws', 'third-party']


class NoteSchema(Schema):
    date = fields.Date()
    text = fields.Str(required=True)


class RoleSchema(Schema):
    policyUrl = fields.Str()
    roleName = fields.Str()
    id = fields.Str(required=True)
    secondaryApprover = fields.Str(default=None, missing=None)
    googleGroup = fields.Str(required=True)


class AccountStatusSchema(Schema):
    region = fields.Str(required=True)
    status = fields.Str(validate=OneOf(ACCOUNT_STATUSES), missing='created')
    notes = fields.Nested(NoteSchema, many=True, missing=[])


class ServiceStatusSchema(Schema):
    region = fields.Str(required=True)
    enabled = fields.Boolean(missing=False)
    notes = fields.Nested(NoteSchema, many=True, missing=[])


class ServiceSchema(Schema):
    name = fields.Str(required=True)
    status = fields.Nested(ServiceStatusSchema, many=True, required=True)
    roles = fields.Nested(RoleSchema, many=True, missing=[])
    metadata = fields.Dict(missing={})


class AccountSchema(Schema):
    schemaVersion = fields.Str(missing='2')
    id = fields.Str(required=True)
    name = fields.Str(required=True)
    contacts = fields.List(fields.Email(), required=True, missing=[])
    provider = fields.Str(validate=OneOf(PROVIDERS), missing='aws')
    type = fields.Str(validate=OneOf(ACCOUNT_TYPES), missing='service')
    tags = fields.List(fields.Str(), missing=[])
    status = fields.Nested(AccountStatusSchema, many=True, missing=[])
    email = fields.Email(required=True)
    environment = fields.Str(validate=OneOf(ACCOUNT_ENVIRONMENTS), missing='prod')
    services = fields.Nested(ServiceSchema, many=True, missing=[])
    sensitive = fields.Bool(missing=False)
    description = fields.Str(required=True)
    owner = fields.Str(validate=OneOf(ACCOUNT_OWNERS), required=True, missing='netflix')
    aliases = fields.List(fields.Str(), missing=[])


