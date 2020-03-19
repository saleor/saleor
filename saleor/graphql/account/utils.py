from typing import TYPE_CHECKING, List

from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat
from graphene.utils.str_converters import to_camel_case

from ...account import events as account_events
from ...account.error_codes import AccountErrorCode

if TYPE_CHECKING:
    from django.contrib.auth.models import Group
    from ...account.models import User


class UserDeleteMixin:
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        user = info.context.user
        if instance == user:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "You cannot delete your own account.",
                        code=AccountErrorCode.DELETE_OWN_ACCOUNT,
                    )
                }
            )
        elif instance.is_superuser:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete this account.",
                        code=AccountErrorCode.DELETE_SUPERUSER_ACCOUNT,
                    )
                }
            )


class CustomerDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if instance.is_staff:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete a staff account.",
                        code=AccountErrorCode.DELETE_STAFF_ACCOUNT,
                    )
                }
            )

    @classmethod
    def post_process(cls, info, deleted_count=1):
        account_events.staff_user_deleted_a_customer_event(
            staff_user=info.context.user, deleted_count=deleted_count
        )


class StaffDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if not instance.is_staff:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete a non-staff user.",
                        code=AccountErrorCode.DELETE_NON_STAFF_USER,
                    )
                }
            )


def get_required_fields_camel_case(required_fields: set) -> set:
    """Return set of AddressValidationRules required fields in camel case."""
    return {validation_field_to_camel_case(field) for field in required_fields}


def validation_field_to_camel_case(name: str) -> str:
    """Convert name of the field from snake case to camel case."""
    name = to_camel_case(name)
    if name == "streetAddress":
        return "streetAddress1"
    return name


def get_allowed_fields_camel_case(allowed_fields: set) -> set:
    """Return set of AddressValidationRules allowed fields in camel case."""
    fields = {validation_field_to_camel_case(field) for field in allowed_fields}
    if "streetAddress1" in fields:
        fields.add("streetAddress2")
    return fields


def get_out_of_scope_permissions(user: "User", permissions: List[str]):
    """Return permissions that the user hasn't got."""
    missing_permissions = []
    for perm in permissions:
        if not user.has_perm(perm):
            missing_permissions.append(perm)
    return missing_permissions


def can_user_manage_group(user: "User", group: "Group"):
    """User can't manage a group with permission that is out of the user's scope."""
    permissions = group.permissions.annotate(
        lookup_field=Concat("content_type__app_label", Value("."), "codename")
    ).values_list("lookup_field", flat=True)
    return user.has_perms(permissions)
