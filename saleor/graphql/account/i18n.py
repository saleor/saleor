from django.core.exceptions import ValidationError

from ...account.forms import get_address_form
from ...account.models import Address
from ...account.validators import validate_possible_number


class I18nMixin:
    """A mixin providing methods necessary to fulfill the internationalization process.

    It is to be used with BaseMutation or ModelMutation.
    """

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        pass

    @classmethod
    def clean_instance(cls, info, instance):
        pass

    @classmethod
    def validate_address_form(cls, address_data: dict, instance=None):
        phone = address_data.get("phone", None)
        if phone:
            try:
                validate_possible_number(phone, address_data.get("country"))
            except ValidationError as exc:
                raise ValidationError(
                    {
                        "phone": ValidationError(
                            f"'{phone}' is not a valid phone number.", code=exc.code
                        )
                    }
                ) from exc

        address_form, _ = get_address_form(
            address_data, address_data.get("country"), instance=instance
        )
        if not address_form.is_valid():
            raise ValidationError(address_form.errors.as_data())
        return address_form

    @classmethod
    def validate_address(cls, address_data: dict, instance=None, info=None):
        if address_data.get("country") is None:
            raise ValidationError(
                {"country": ValidationError("This field is required.", code="required")}
            )
        address_form = cls.validate_address_form(address_data)
        if not instance:
            instance = Address()

        cls.construct_instance(instance, address_form.cleaned_data)
        cls.clean_instance(info, instance)
        return instance
