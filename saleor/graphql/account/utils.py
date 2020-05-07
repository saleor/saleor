from collections import defaultdict
from typing import TYPE_CHECKING, List, Optional, Set, Union

import graphene
from django.contrib.auth.models import Group, Permission
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ValidationError
from django.db.models import Q, Value
from django.db.models.functions import Concat
from graphene.utils.str_converters import to_camel_case

from ...account import events as account_events
from ...account.error_codes import AccountErrorCode
from ...core.permissions import AccountPermissions, get_permissions

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from ...account.models import User
    from ...app.models import App


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
        errors = defaultdict(list)
        requestor = info.context.user
        cls.check_if_users_can_be_deleted(info, [instance], "id", errors)
        cls.check_if_requestor_can_manage_users(requestor, [instance], "id", errors)
        cls.check_if_removing_left_not_manageable_permissions(
            requestor, [instance], "id", errors
        )
        if errors:
            raise ValidationError(errors)

    @classmethod
    def check_if_users_can_be_deleted(cls, info, instances, field, errors):
        """Check if only staff users will be deleted. Cannot delete non-staff users."""
        not_staff_users = set()
        for user in instances:
            if not user.is_staff:
                not_staff_users.add(user)
            try:
                super().clean_instance(info, user)
            except ValidationError as error:
                errors["ids"].append(error)

        if not_staff_users:
            user_pks = [
                graphene.Node.to_global_id("User", user.pk) for user in not_staff_users
            ]
            msg = "Cannot delete a non-staff users."
            code = AccountErrorCode.DELETE_NON_STAFF_USER
            params = {"users": user_pks}
            errors[field].append(ValidationError(msg, code=code, params=params))

    @classmethod
    def check_if_requestor_can_manage_users(cls, requestor, instances, field, errors):
        """Requestor can't manage users with wider scope of permissions."""
        if requestor.is_superuser:
            return
        out_of_scope_users = get_out_of_scope_users(requestor, instances)
        if out_of_scope_users:
            user_pks = [
                graphene.Node.to_global_id("User", user.pk)
                for user in out_of_scope_users
            ]
            msg = "You can't manage this users."
            code = AccountErrorCode.OUT_OF_SCOPE_USER.value
            params = {"users": user_pks}
            error = ValidationError(msg, code=code, params=params)
            errors[field] = error

    @classmethod
    def check_if_removing_left_not_manageable_permissions(
        cls, requestor, users, field, errors
    ):
        """Check if after removing users all permissions will be manageable.

        After removing users, for each permission, there should be at least one
        active staff member who can manage it (has both “manage staff” and
        this permission).
        """
        if requestor.is_superuser:
            return
        permissions = get_not_manageable_permissions_when_deactivate_or_remove_users(
            users
        )
        if permissions:
            # add error
            msg = "Users cannot be removed, some of permissions will not be manageable."
            code = AccountErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permissions}
            error = ValidationError(msg, code=code, params=params)
            errors[field] = error


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


def get_user_permissions(user: "User") -> "QuerySet":
    """Return all user permissions - from user groups and user_permissions field."""
    if user.is_superuser:
        return get_permissions()
    groups = user.groups.all()
    user_permissions = user.user_permissions.all()
    group_permissions = Permission.objects.filter(group__in=groups)
    permissions = user_permissions | group_permissions
    return permissions


def get_out_of_scope_permissions(
    requestor: Union["User", "App"], permissions: List[str]
) -> List[str]:
    """Return permissions that the requestor hasn't got."""
    missing_permissions = []
    for perm in permissions:
        if not requestor.has_perm(perm):
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


def can_user_manage_group(user: "User", group: Group) -> bool:
    """User can't manage a group with permission that is out of the user's scope."""
    permissions = get_group_permission_codes(group)
    return user.has_perms(permissions)


def can_manage_app(requestor: Union["User", "App"], app: "App") -> bool:
    """Requestor can't manage app with wider scope of permissions."""
    permissions = app.get_permissions()
    return requestor.has_perms(permissions)


def get_group_permission_codes(group: Group) -> "QuerySet":
    """Return group permissions in the format '<app label>.<permission codename>'."""
    return group.permissions.annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    ).values_list("formated_codename", flat=True)


def get_groups_which_user_can_manage(user: "User") -> List[Optional[Group]]:
    """Return groups which user can manage."""
    if not user.is_staff:
        return []

    user_permissions = get_user_permissions(user)
    user_permission_pks = set(user_permissions.values_list("pk", flat=True))

    groups = Group.objects.all().annotate(group_perms=ArrayAgg("permissions"))

    editable_groups = []
    for group in groups.iterator():
        out_of_scope_permissions = set(group.group_perms) - user_permission_pks
        out_of_scope_permissions.discard(None)
        if not out_of_scope_permissions:
            editable_groups.append(group)

    return editable_groups


def get_not_manageable_permissions_when_deactivate_or_remove_users(users: List["User"]):
    """Return permissions that cannot be managed after deactivating or removing users.

    After removing or deactivating users, for each user permission which he can manage,
    there should be at least one active staff member who can manage it
    (has both “manage staff” and this permission).
    """
    # check only users who can manage permissions
    users_to_check = {
        user for user in users if user.has_perm(AccountPermissions.MANAGE_STAFF.value)
    }

    if not users_to_check:
        return set()

    user_pks = set()
    not_manageable_permissions = set()
    for user in users_to_check:
        not_manageable_permissions.update(user.get_all_permissions())
        user_pks.add(user.pk)

    groups_data = get_group_to_permissions_and_users_mapping()

    # get users from groups with manage staff
    manage_staff_users = get_users_and_look_for_permissions_in_groups_with_manage_staff(
        groups_data, set()
    )

    if not manage_staff_users:
        return not_manageable_permissions

    # remove deactivating or removing users from manage staff users
    manage_staff_users = manage_staff_users - user_pks

    # look for not_manageable_permissions in user with manage staff permissions groups,
    # if any of not_manageable_permissions is found it is removed from set
    look_for_permission_in_users_with_manage_staff(
        groups_data, manage_staff_users, not_manageable_permissions
    )

    # return remaining not managable permissions
    return not_manageable_permissions


def get_not_manageable_permissions_after_removing_perms_from_group(
    group: Group, permissions: List["str"]
):
    """Return permissions that cannot be managed after removing permissions from group.

    After removing permissions from group, for each permission, there should be at least
    one staff member who can manage it (has both “manage staff” and this permission).
    """
    groups_data = get_group_to_permissions_and_users_mapping()
    groups_data.pop(group.pk)
    not_manageable_permissions = set(permissions)

    return get_not_manageable_permissions(groups_data, not_manageable_permissions)


def get_not_manageable_permissions_after_removing_users_from_group(
    group: Group, users: List["User"]
):
    """Return permissions that cannot be managed after removing users from group.

    After removing users from group, for each permission, there should be at least
    one staff member who can manage it (has both “manage staff” and this permission).
    """
    group_users = group.user_set.all()
    group_permissions = group.permissions.values_list("codename", flat=True)
    # if group has manage_staff permission and some users will stay in group
    # given users can me removed (permissions will be manageable)
    manage_staff_codename = AccountPermissions.MANAGE_STAFF.codename
    if len(group_users) > len(users) and manage_staff_codename in group_permissions:
        return set()

    # check if any of remaining group user has manage staff permission
    # if True, all group permissions can be managed
    group_remaining_users = set(group_users) - set(users)
    manage_staff_permission = AccountPermissions.MANAGE_STAFF.value
    if any([user.has_perm(manage_staff_permission) for user in group_remaining_users]):
        return set()

    # if group and any of remaining group user doesn't have manage staff permission
    # we can treat the situation as this when group is removing
    not_manageable_permissions = get_not_manageable_permissions_after_group_deleting(
        group
    )

    return not_manageable_permissions


def get_not_manageable_permissions_after_group_deleting(group):
    """Return permissions that cannot be managed after deleting the group.

    After removing group, for each permission, there should be at least one staff member
    who can manage it (has both “manage staff” and this permission).
    """
    groups_data = get_group_to_permissions_and_users_mapping()
    not_manageable_permissions = groups_data.pop(group.pk)["permissions"]
    return get_not_manageable_permissions(groups_data, not_manageable_permissions)


def get_not_manageable_permissions(
    groups_data: dict, not_manageable_permissions: Set[str],
):
    # get users from groups with manage staff and look for not_manageable_permissions
    # if any of not_manageable_permissions is found it is removed from set
    manage_staff_users = get_users_and_look_for_permissions_in_groups_with_manage_staff(
        groups_data, not_manageable_permissions
    )

    # check if management of all permissions provided by other groups
    if not not_manageable_permissions:
        return set()

    # check lack of users with manage staff in other groups
    if not manage_staff_users:
        return not_manageable_permissions

    # look for remaining permissions from not_manageable_permissions in user with
    # manage staff permissions groups, if any of not_manageable_permissions is found
    # it is removed from set
    look_for_permission_in_users_with_manage_staff(
        groups_data, manage_staff_users, not_manageable_permissions
    )

    # return remaining not managable permissions
    return not_manageable_permissions


def get_group_to_permissions_and_users_mapping():
    """Return group mapping with data about their permissions and user.

    Get all groups and return mapping in structure:
        {
            group1_pk: {
                "permissions": ["perm_codename1", "perm_codename2"],
                "users": [user_pk1, user_pk2]
            },
        }
    """
    mapping = {}
    groups_data = (
        Group.objects.all()
        .annotate(
            perm_codenames=ArrayAgg(
                Concat(
                    "permissions__content_type__app_label",
                    Value("."),
                    "permissions__codename",
                ),
                filter=Q(permissions__isnull=False),
            ),
            users=ArrayAgg("user", filter=Q(user__is_active=True)),
        )
        .values("pk", "perm_codenames", "users")
    )

    for data in groups_data:
        mapping[data["pk"]] = {
            "permissions": set(data["perm_codenames"]),
            "users": set(data["users"]),
        }

    return mapping


def get_users_and_look_for_permissions_in_groups_with_manage_staff(
    groups_data: dict, permissions_to_find: Set[str],
):
    """Search for permissions in groups with manage staff and return their users.

    Args:
        groups_data: dict with groups data, key is a group pk and value is group data
            with permissions and users
        permissions_to_find: searched permissions

    """
    users_with_manage_staff: Set[int] = set()
    for data in groups_data.values():
        permissions = data["permissions"]
        users = data["users"]
        has_manage_staff = AccountPermissions.MANAGE_STAFF.value in permissions
        has_users = bool(users)
        # only consider groups with active users and manage_staff permission
        if has_users and has_manage_staff:
            common_permissions = permissions_to_find & permissions
            # remove found permission from set
            permissions_to_find.difference_update(common_permissions)
            users_with_manage_staff.update(users)

    return users_with_manage_staff


def look_for_permission_in_users_with_manage_staff(
    groups_data: dict, users_to_check: Set[int], permissions_to_find: Set[str],
):
    """Search for permissions in user with manage staff groups.

    Args:
        groups_data: dict with groups data, key is a group pk and value is group data
            with permissions and users
        users_to_check: users with manage_staff
        permissions_to_find: searched permissions

    """
    for data in groups_data.values():
        permissions = data["permissions"]
        users = data["users"]
        common_users = users_to_check & users
        if common_users:
            common_permissions = permissions_to_find & permissions
            # remove found permission from set
            permissions_to_find.difference_update(common_permissions)
