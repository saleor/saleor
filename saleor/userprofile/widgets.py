from django.forms import Select, TextInput
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

from .validators import validate_possible_number


phone_prefixes = [
    ('+{}'.format(k), '+{}'.format(k)) for
    (k, v) in sorted(COUNTRY_CODE_TO_REGION_CODE.items())]


class PhonePrefixWidget(PhoneNumberPrefixWidget):
    """
    Overwrite widget to use choices with tuple in a simple form of "+XYZ: +XYZ"
    Workaround for an issue:
    https://github.com/stefanfoulis/django-phonenumber-field/issues/82
    """

    template_name = 'userprofile/snippets/phone_prefix_widget.html'

    def __init__(self, attrs=None):
        widgets = (Select(attrs=attrs, choices=phone_prefixes), TextInput())
        super(PhoneNumberPrefixWidget, self).__init__(widgets, attrs)
