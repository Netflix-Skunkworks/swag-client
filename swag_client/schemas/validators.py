"""
.. module:: swag_client.schemas.validators
    :platform: Unix
.. author:: Kevin Glisson (kglisson@netflix.com)
.. author:: Mike Grima (mgrima@netflix.com)
"""
from marshmallow.validate import Validator
from marshmallow.exceptions import ValidationError


def validate_fqdn(n):
    if '.' not in n:
        raise ValidationError("{0} is not a FQDN".format(n))


class IsDigit(Validator):
    def __call__(self, value):
        if not value.isdigit():
            raise ValidationError("Must be a string of digits: {}".format(value))
        return True
