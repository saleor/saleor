from typing import Dict, Optional

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
    def validate_address_form(
        cls,
        address_data: dict,
        address_type: Optional[str] = None,
        instance=None,
        format_check=True,
        required_check=True,
        enable_normalization=True,
    ):
        phone = address_data.get("phone", None)
        params = {"address_type": address_type} if address_type else {}
        if phone:
            try:
                validate_possible_number(phone, address_data.get("country"))
            except ValidationError as exc:
                if format_check:
                    raise ValidationError(
                        {
                            "phone": ValidationError(
                                f"'{phone}' is not a valid phone number.",
                                code=exc.code,
                                params=params,
                            )
                        }
                    ) from exc

        address_form, _ = get_address_form(
            address_data,
            address_data.get("country"),
            instance=instance,
            enable_normalization=enable_normalization,
        )
        if not address_form.is_valid():
            errors = cls.attach_params_to_address_form_errors(
                address_form, params, format_check, required_check
            )
            if errors:
                raise ValidationError(errors)
        return address_form

    @classmethod
    def attach_params_to_address_form_errors(
        cls,
        address_form,
        params: Dict[str, str],
        values_check=True,
        required_check=True,
    ):
        address_errors_dict = address_form.errors.as_data()
        errors_dict = {}
        for field, errors in address_errors_dict.items():
            for error in errors:
                if not error.params:
                    error.params = params
                else:
                    error.params.update(params)
                if error.code != "required":
                    if values_check:
                        errors_dict[field] = errors
                    else:
                        address_form.cleaned_data[field] = address_form.data[field]
                if error.code == "required":
                    field_value = address_form.data.get(field)
                    if required_check:
                        errors_dict[field] = errors
                    elif field_value is not None:
                        address_form.cleaned_data[field] = field_value

        return errors_dict

    @classmethod
    def validate_address(
        cls,
        address_data: dict,
        *,
        address_type: Optional[str] = None,
        instance: Optional[Address] = None,
        info=None,
        format_check=True,
        required_check=True,
        enable_normalization=True
    ):
        if address_data.get("country") is None:
            params = {"address_type": address_type} if address_type else {}
            raise ValidationError(
                {
                    "country": ValidationError(
                        "This field is required.", code="required", params=params
                    )
                }
            )
        address_form = cls.validate_address_form(
            address_data,
            address_type,
            format_check=format_check,
            required_check=required_check,
            enable_normalization=enable_normalization,
        )
        if not instance:
            instance = Address()

        cls.construct_instance(instance, address_form.cleaned_data)
        cls.clean_instance(info, instance)
        return instance
