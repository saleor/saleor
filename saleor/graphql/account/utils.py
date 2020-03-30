from typing import TYPE_CHECKING, List

from django.contrib.auth.models import Permission
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


def get_user_permissions(user: "User"):
    """Return all user permissions - from user groups and user_permissions field."""
    groups = user.groups.all()
    user_permissions = user.user_permissions.all()
    group_permissions = Permission.objects.filter(group__in=groups)
    permissions = user_permissions | group_permissions
    return permissions


def get_out_of_scope_permissions(user: "User", permissions: List[str]):
    """Return permissions that the user hasn't got."""
    missing_permissions = []
    for perm in permissions:
        if not user.has_perm(perm):
            missing_permissions.append(perm)
    return missing_permissions


def get_out_of_scope_users(root_user: "User", users: List["User"]):
    """Return users whose permission scope is wider than the given user."""
    out_of_scope_users = []
    for user in users:
        user_permissions = user.get_all_permissions()
        if not root_user.has_perms(user_permissions):
            out_of_scope_users.append(user)
    return out_of_scope_users


def can_user_manage_group(user: "User", group: "Group"):
    """User can't manage a group with permission that is out of the user's scope."""
    permissions = get_group_permission_codes(group)
    return user.has_perms(permissions)


def get_group_permission_codes(group: "Group"):
    """Return group permissions in the format '<app label>.<permission codename>'."""
    return group.permissions.annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    ).values_list("formated_codename", flat=True)
