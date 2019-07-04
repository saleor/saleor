from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.phonenumber import to_python
from phonenumbers.phonenumberutil import is_possible_number


def validate_possible_number(value, country=None):
    phone_number = to_python(value, country)
    if phone_number and not is_possible_number(phone_number):
        raise ValidationError(
            _("The phone number entered is not valid."), code="invalid_phone_number"
        )
