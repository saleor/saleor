from django.core.exceptions import ValidationError

from ...account.forms import get_address_form
from ...account.models import Address
from ...account.validators import validate_possible_number
from ...core.exceptions import PermissionDenied
from ...core.utils.metadata_manager import MetadataItem
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import (
    AccountPermissions,
    BasePermissionEnum,
    CheckoutPermissions,
    OrderPermissions,
    ProductPermissions,
    SitePermissions,
)
from ...permission.utils import all_permissions_required
from ..core import ResolveInfo

SKIP_ADDRESS_VALIDATION_PERMISSION_MAP: dict[str, list[BasePermissionEnum]] = {
    "addressCreate": [AccountPermissions.MANAGE_USERS],
    "addressUpdate": [AccountPermissions.MANAGE_USERS],
    "customerBulkUpdate": [AccountPermissions.MANAGE_USERS],
    "draftOrderCreate": [OrderPermissions.MANAGE_ORDERS],
    "draftOrderUpdate": [OrderPermissions.MANAGE_ORDERS],
    "orderUpdate": [OrderPermissions.MANAGE_ORDERS],
    "orderBulkCreate": [OrderPermissions.MANAGE_ORDERS_IMPORT],
    "createWarehouse": [ProductPermissions.MANAGE_PRODUCTS],
    "updateWarehouse": [ProductPermissions.MANAGE_PRODUCTS],
    "shopAddressUpdate": [SitePermissions.MANAGE_SETTINGS],
    "checkoutCreate": [
        CheckoutPermissions.HANDLE_CHECKOUTS,
        AuthorizationFilters.AUTHENTICATED_APP,
    ],
    "checkoutShippingAddressUpdate": [
        CheckoutPermissions.HANDLE_CHECKOUTS,
        AuthorizationFilters.AUTHENTICATED_APP,
    ],
    "checkoutBillingAddressUpdate": [
        CheckoutPermissions.HANDLE_CHECKOUTS,
        AuthorizationFilters.AUTHENTICATED_APP,
    ],
    "accountAddressCreate": [
        AuthorizationFilters.AUTHENTICATED_APP,
        AccountPermissions.IMPERSONATE_USER,
    ],
    "accountUpdate": [
        AuthorizationFilters.AUTHENTICATED_APP,
        AccountPermissions.IMPERSONATE_USER,
    ],
    "accountAddressUpdate": [
        AccountPermissions.MANAGE_USERS,
        AuthorizationFilters.AUTHENTICATED_APP,
    ],
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
    def _validate_address_form(
        cls,
        address_data: dict,
        address_type: str | None = None,
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
        validation_skipped = False
        if not address_form.is_valid():
            validation_skipped = True
            errors = cls.attach_params_to_address_form_errors(
                address_form, params, format_check, required_check
            )
            if errors:
                raise ValidationError(errors)

        if address_form.cleaned_data["metadata"] is None:
            address_form.cleaned_data["metadata"] = {}
        if address_form.cleaned_data["private_metadata"] is None:
            address_form.cleaned_data["private_metadata"] = {}
        address_form.cleaned_data["validation_skipped"] = validation_skipped

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
        address_type: str | None = None,
        instance: Address | None = None,
        info=None,
        format_check=True,
        required_check=True,
        enable_normalization=True,
    ) -> Address:
        if address_data.get("country") is None:
            params = {"address_type": address_type} if address_type else {}
            raise ValidationError(
                {
                    "country": ValidationError(
                        "This field is required.", code="required", params=params
                    )
                }
            )

        if address_data.get("skip_validation"):
            cls.can_skip_address_validation(info)
            format_check = False

        address_form = cls._validate_address_form(
            address_data,
            address_type,
            format_check=format_check,
            required_check=required_check,
            enable_normalization=enable_normalization,
        )
        address_data = address_form.cleaned_data

        if not instance:
            instance = Address()

        cls.construct_instance(instance, address_data)
        cls.clean_instance(info, instance)
        return instance

    @classmethod
    def can_skip_address_validation(cls, info: ResolveInfo | None):
        required_permissions = None
        if info:
            mutation_name = info.field_name
            required_permissions = SKIP_ADDRESS_VALIDATION_PERMISSION_MAP.get(
                mutation_name
            )

        if not required_permissions:
            raise ValidationError(
                {
                    "skip_validation": ValidationError(
                        "This mutation doesn't allow to skip address validation.",
                        code="invalid",
                    )
                }
            )
        if info and not all_permissions_required(info.context, required_permissions):
            raise PermissionDenied(
                f"To skip address validation, you need following permissions: "
                f"{', '.join(perm.name for perm in required_permissions)}.",
            )

    @classmethod
    def is_address_modified(
        cls, instance: Address | None, address_data: dict | None
    ) -> bool:
        """Compare address instance with address input.

        Args:
            instance: Address model instance
            address_data: Address input data with snake case keys

        Return:
            True, if at least one field has changed.
            False otherwise.

        """
        # TODO zedzior: check if address data = {}
        if address_data is None or not instance:
            return False

        address_as_dict = instance.as_data()
        skip_validation = address_as_dict.pop("validation_skipped")
        address_as_dict["skip_validation"] = skip_validation

        for key, value in address_data.items():
            if key == "metadata":
                value = cls._metadata_input_as_dict(value)
            if value != address_as_dict.get(key):
                return True

        return False

    @classmethod
    def _metadata_input_as_dict(
        cls, metadata_input: list[MetadataItem]
    ) -> dict[str, str]:
        # TODO zedzior check how to delete metadata
        if not metadata_input:
            return {}

        metadata_dict = {}
        for item in metadata_input:
            metadata_dict[item.key] = item.value

        return metadata_dict
