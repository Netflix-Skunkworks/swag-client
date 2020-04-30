from datetime import datetime
from marshmallow import Schema, fields, validates_schema
from marshmallow.exceptions import ValidationError
from marshmallow.validate import OneOf


PROVIDERS = ['aws', 'gcp', 'azure']
ACCOUNT_STATUSES = ['created', 'in-progress', 'ready', 'deprecated', 'deleted', 'in-active']


class NoteSchema(Schema):
    date = fields.Str()
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


class RegionSchema(Schema):
    status = fields.Str(validate=OneOf(ACCOUNT_STATUSES), missing='created')
    az_mapping = fields.Dict()


class AccountSchema(Schema):
    schemaVersion = fields.Str(missing='2')
    id = fields.Str(required=True)
    name = fields.Str(required=True)
    contacts = fields.List(fields.Email(), missing=[])
    provider = fields.Str(validate=OneOf(PROVIDERS), missing='aws')
    type = fields.Str(missing='service')
    tags = fields.List(fields.Str(), missing=[])
    status = fields.Nested(AccountStatusSchema, many=True, missing=[])
    email = fields.Email(required=True)
    environment = fields.Str(missing='prod')
    services = fields.Nested(ServiceSchema, many=True, missing=[])
    sensitive = fields.Bool(missing=False)
    description = fields.Str(required=True)
    owner = fields.Str(missing='netflix')
    aliases = fields.List(fields.Str(), missing=[])
    account_status = fields.Str(validate=OneOf(ACCOUNT_STATUSES), missing='created')
    domain = fields.Str()
    sub_domain = fields.Str()
    regions = fields.Dict()
    org_id = fields.Str()

    @validates_schema
    def validate_type(self, data, partial=False, many=False, unknown=False):
        """Performs field validation against the schema context
        if values have been provided to SWAGManager via the
        swag.schema_context config object.

        If the schema context for a given field is empty, then
        we assume any value is valid for the given schema field.
        """
        fields_to_validate = ['type', 'environment', 'owner']
        for field in fields_to_validate:
            value = data.get(field)
            allowed_values = self.context.get(field)
            if allowed_values and value not in allowed_values:
                raise ValidationError('Must be one of {}'.format(allowed_values), field_names=field)

    @validates_schema
    def validate_account_status(self, data, partial=False, many=False, unknown=False):
        """Performs field validation for account_status.  If any
        region is not deleted, account_status cannot be deleted
        """
        deleted_status = 'deleted'
        region_status = data.get('status')
        account_status = data.get('account_status')
        for region in region_status:
            if region['status'] != deleted_status and account_status == deleted_status:
                raise ValidationError('Account Status cannot be "deleted" if a region is not "deleted"')

    @validates_schema
    def validate_regions_schema(self, data, partial=False, many=False, unknown=False):
        """Performs field validation for regions.  This should be
        a dict with region names as the key and RegionSchema as the value
        """
        region_schema = RegionSchema()
        supplied_regions = data.get('regions', {})
        for region in supplied_regions.keys():
            result = region_schema.validate(supplied_regions[region])
            if len(result.keys()) > 0:
                raise ValidationError(result)

