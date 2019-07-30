from django.core.exceptions import ValidationError
from django_countries import countries

from ...account.forms import get_address_form
from ...account.models import Address
from ...account.validators import validate_possible_number


class I18nMixin:
    """A mixin providing methods necessary to fulfill the internationalization process.

    It is to be used with BaseMutation or ModelMutation.
    """

    @classmethod
    def validate_address(cls, address_data: dict, instance=None):
        phone = address_data.get("phone", None)
        if phone:
            try:
                validate_possible_number(phone, address_data.get("country"))
            except ValidationError as exc:
                raise ValidationError(
                    {"phone": f"'{phone}' is not a valid phone number."}
                ) from exc

        country_code = address_data.get("country")
        if country_code in countries.countries.keys():
            address_form, _ = get_address_form(address_data, address_data["country"])
        else:
            raise ValidationError({"country": "Invalid country code."})

        if not address_form.is_valid():
            raise ValidationError(address_form.errors)

        if not instance:
            instance = Address()

        cls.construct_instance(instance, address_form.cleaned_data)
        cls.clean_instance(instance)
        return instance
