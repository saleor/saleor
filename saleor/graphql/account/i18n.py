from typing import Optional

from django.core.exceptions import ValidationError

from ...account.forms import get_address_form
from ...account.models import Address
from ...account.validators import validate_possible_number
from ...permission.enums import (
    AccountPermissions,
    BasePermissionEnum,
    OrderPermissions,
    ProductPermissions,
)
from ..core import ResolveInfo
from ..utils import get_user_or_app_from_context

SKIP_ADDRESS_VALIDATION_PERMISSION_MAP: dict[str, list[BasePermissionEnum]] = {
    "addressCreate": [AccountPermissions.MANAGE_USERS],
    "addressUpdate": [AccountPermissions.MANAGE_USERS],
    "draftOrderCreate": [OrderPermissions.MANAGE_ORDERS],
    "draftOrderUpdate": [OrderPermissions.MANAGE_ORDERS],
    "createWarehouse": [ProductPermissions.MANAGE_PRODUCTS],
}


class I18nMixin:
    """A mixin providing methods necessary to fulfill the internationalization process.

    It is to be used with BaseMutation or ModelMutation.
    """

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        pass

    @classmethod
    def clean_instance(cls, _info: ResolveInfo, _instance):
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

        address_form = get_address_form(
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

        if address_form.cleaned_data["metadata"] is None:
            address_form.cleaned_data["metadata"] = {}
        if address_form.cleaned_data["private_metadata"] is None:
            address_form.cleaned_data["private_metadata"] = {}

        return address_form

    @classmethod
    def attach_params_to_address_form_errors(
        cls,
        address_form,
        params: dict[str, str],
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
        enable_normalization=True,
    ):
        if address_data.get("skip_validation"):
            cls.can_skip_address_validation(info)
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

    @classmethod
    def can_skip_address_validation(cls, info: ResolveInfo):
        requester = get_user_or_app_from_context(info.context)
        mutation_name = info.field_name
        required_permissions = SKIP_ADDRESS_VALIDATION_PERMISSION_MAP.get(mutation_name)
        if not required_permissions:
            raise ValidationError(
                {
                    "skip_validation": ValidationError(
                        "This mutation doesn't allow to skip address validation.",
                        code="invalid",
                    )
                }
            )
        elif not requester or not requester.has_perms(required_permissions):
            raise ValidationError(
                {
                    "skip_validation": ValidationError(
                        f"To skip address validation, you need following permissions: "
                        f"{','.join(perm.name for perm in required_permissions)}.",
                        code="required",
                    )
                }
            )
