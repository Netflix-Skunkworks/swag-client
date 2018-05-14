"""
.. module:: swag_client.schemas.v1
    :platform: Unix
.. author:: Kevin Glisson (kglisson@netflix.com)
.. author:: Mike Grima (mgrima@netflix.com)
"""
from marshmallow import Schema, fields, validates_schema
from marshmallow.validate import Length, OneOf

from swag_client.schemas.validators import validate_fqdn


class AWSAccountSchema(Schema):
    account_number = fields.String(required=True, validate=Length(max=12, min=12))  # equal keyword not yet available in mainline marshmallow
    cloudtrail_index = fields.String()
    cloudtrail_kibana_url = fields.String()
    s3_name = fields.String()
    email = fields.Email(required=True)


class GoogleProjectSchema(Schema):
    project_id = fields.String(required=True, validate=Length(max=30))
    project_number = fields.Integer(required=True)
    project_name = fields.String(required=True)


TYPES = {'aws': AWSAccountSchema, 'gcp': GoogleProjectSchema}


# Here are define top level fields that every account would need
class AccountSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    type = fields.String(required=True, validate=OneOf(TYPES.keys()))
    metadata = fields.Dict(required=True)
    tags = fields.List(fields.String())
    services = fields.Dict()
    cmc_required = fields.Boolean(required=True)
    description = fields.String(required=True)
    owners = fields.List(fields.Email(required=True), required=True)
    alias = fields.List(fields.String(), required=True)
    bastion = fields.String(validate=validate_fqdn)

    # Set to True if your company owns the account.
    # Set to False if this is a partner account your apps may need to know about.
    ours = fields.Boolean(required=True)

    schema_version = fields.Integer(required=True, missing='v1')
    account_status = fields.String(missing='created')

    @validates_schema
    def validate_metadata(self, data):
        TYPES[data['type']](many=True, strict=True).load([data['metadata']])
