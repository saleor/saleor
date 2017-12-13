from phonenumber_field.formfields import (
    PhoneNumberField as PhoneNumberFormField)
from phonenumber_field.modelfields import (
    PhoneNumberField as PhoneNumberModelField)

from .validators import validate_possible_number


class PossiblePhoneNumberModelField(PhoneNumberModelField):
    """
    Less strict rule for phone numbers written to database.
    """
    default_validators = [validate_possible_number]


class PossiblePhoneNumberFormField(PhoneNumberFormField):
    """
    Modify PhoneNumberField form field to allow using phone numbers from
    countries other than selected one.
    To achieve this both default_validator attribute and to_python method needs
    to be overwritten.
    """

    default_validators = [validate_possible_number]

    def to_python(self, value):
        return value
