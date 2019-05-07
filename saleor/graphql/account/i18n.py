from django_countries import countries
from django.core.exceptions import ValidationError

from ...account.forms import get_address_form
from ...account.models import Address


class I18nMixin:
    """Mixin to be used with BaseMutation or ModelMutation, providing methods
    necessary to fulfill the internationalization process.
    """

    @classmethod
    def validate_address(cls, address_data, instance=None):
        country_code = address_data.get('country')
        if country_code in countries.countries.keys():
            address_form, _ = get_address_form(
                address_data, address_data['country'])
        else:
            raise ValidationError({'country': 'Invalid country code.'})

        if not address_form.is_valid():
            raise ValidationError(address_form.errors)

        if not instance:
            instance = Address()

        cls.construct_instance(instance, address_form.cleaned_data)
        cls.clean_instance(instance)
        return instance
