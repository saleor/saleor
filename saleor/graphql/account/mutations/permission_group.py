from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple, cast

import graphene
from django.core.exceptions import ValidationError

from ....account import models
from ....account.error_codes import PermissionGroupErrorCode
from ....account.models import User
from ....core.exceptions import PermissionDenied
from ....core.tracing import traced_atomic_transaction
from ....permission.enums import AccountPermissions, get_permissions
from ...account.utils import (
    can_user_manage_group,
    get_not_manageable_permissions_after_group_deleting,
    get_not_manageable_permissions_after_removing_perms_from_group,
    get_not_manageable_permissions_after_removing_users_from_group,
    get_out_of_scope_permissions,
    get_out_of_scope_users,
)
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.enums import PermissionEnum
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types import NonNullList, PermissionGroupError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils.validators import check_for_duplicates
from ..types import Group


class PermissionGroupInput(graphene.InputObjectType):
    add_permissions = NonNullList(
        PermissionEnum,
        description="List of permission code names to assign to this group.",
        required=False,
    )
    add_users = NonNullList(
        graphene.ID,
        description="List of users to assign to this group.",
        required=False,
    )


class PermissionGroupCreateInput(PermissionGroupInput):
    name = graphene.String(description="Group name.", required=True)


class PermissionGroupCreate(ModelMutation):
    class Arguments:
        input = PermissionGroupCreateInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = (
            "Create new permission group. "
            "Apps are not allowed to perform this mutation."
        )
        model = models.Group
        object_type = Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        add_permissions = cleaned_data.get("add_permissions")
        with traced_atomic_transaction():
            if add_permissions:
                instance.permissions.add(*add_permissions)

            users = cleaned_data.get("add_users")
            if users:
                instance.user_set.add(*users)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.permission_group_created, instance)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        user = info.context.user
        user = cast(User, user)
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)
        cls.clean_permissions(user, instance, errors, cleaned_input)
        cls.clean_users(user, errors, cleaned_input, instance)

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_permissions(
        cls,
        requestor: "User",
        group: models.Group,
        errors: Dict[str, List[ValidationError]],
        cleaned_input: dict,
    ):
        field = "add_permissions"
        permission_items = cleaned_input.get(field)
        if permission_items:
            cleaned_input[field] = get_permissions(permission_items)
            if not requestor.is_superuser:
                cls.ensure_can_manage_permissions(
                    requestor, errors, field, permission_items
                )

    @classmethod
    def check_permissions(cls, context, permissions=None):
        app = get_app_promise(context).get()
        if app:
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)

    @classmethod
    def ensure_can_manage_permissions(
        cls,
        requestor: "User",
        errors: Dict[str, List[ValidationError]],
        field: str,
        permission_items: List[str],
    ):
        """Check if requestor can manage permissions from input.

        Requestor cannot manage permissions witch he doesn't have.
        """
        missing_permissions = get_out_of_scope_permissions(requestor, permission_items)
        if missing_permissions:
            # add error
            error_msg = "You can't add permission that you don't have."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
            params = {"permissions": missing_permissions}
            cls.update_errors(errors, error_msg, field, code, params)

    @classmethod
    def clean_users(
        cls,
        requestor: User,
        errors: dict,
        cleaned_input: dict,
        group: models.Group,
    ):
        user_items = cleaned_input.get("add_users")
        if user_items:
            cls.ensure_users_are_staff(errors, "add_users", cleaned_input)

    @classmethod
    def ensure_users_are_staff(
        cls,
        errors: Dict[str, List[ValidationError]],
        field: str,
        cleaned_input: dict,
    ):
        """Ensure all of the users are staff members, raise error if not."""
        users = cleaned_input[field]
        non_staff_users = [user.pk for user in users if not user.is_staff]
        if non_staff_users:
            # add error
            ids = [graphene.Node.to_global_id("User", pk) for pk in non_staff_users]
            error_msg = "User must be staff member."
            code = PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.value
            params = {"users": ids}
            cls.update_errors(errors, error_msg, field, code, params)

    @classmethod
    def update_errors(
        cls,
        errors: Dict[str, List[ValidationError]],
        msg: str,
        field: str,
        code: str,
        params: dict,
    ):
        """Create ValidationError and add it to error list."""
        error = ValidationError(message=msg, code=code, params=params)
        errors[field].append(error)


class PermissionGroupUpdateInput(PermissionGroupInput):
    name = graphene.String(description="Group name.", required=False)
    remove_permissions = NonNullList(
        PermissionEnum,
        description="List of permission code names to unassign from this group.",
        required=False,
    )
    remove_users = NonNullList(
        graphene.ID,
        description="List of users to unassign from this group.",
        required=False,
    )


class PermissionGroupUpdate(PermissionGroupCreate):
    class Arguments:
        id = graphene.ID(description="ID of the group to update.", required=True)
        input = PermissionGroupUpdateInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = (
            "Update permission group. Apps are not allowed to perform this mutation."
        )
        model = models.Group
        object_type = Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            remove_users = cleaned_data.get("remove_users")
            with traced_atomic_transaction():
                if remove_users:
                    instance.user_set.remove(*remove_users)
                remove_permissions = cleaned_data.get("remove_permissions")
                if remove_permissions:
                    instance.permissions.remove(*remove_permissions)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.permission_group_updated, instance)

    @classmethod
    def clean_input(
        cls,
        info,
        instance,
        data,
    ):
        requestor = info.context.user
        cls.ensure_requestor_can_manage_group(requestor, instance)

        errors: DefaultDict[str, List[ValidationError]] = defaultdict(list)
        permission_fields = ("add_permissions", "remove_permissions", "permissions")
        user_fields = ("add_users", "remove_users", "users")

        cls.check_duplicates(errors, data, permission_fields)
        cls.check_duplicates(errors, data, user_fields)

        if errors:
            raise ValidationError(errors)

        cleaned_input = super().clean_input(info, instance, data)

        return cleaned_input

    @classmethod
    def ensure_requestor_can_manage_group(cls, requestor: "User", group: models.Group):
        """Check if requestor can manage group.

        Requestor cannot manage group with wider scope of permissions.
        """
        if not requestor.is_superuser and not can_user_manage_group(requestor, group):
            error_msg = "You can't manage group with permissions out of your scope."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
            raise ValidationError(error_msg, code)

    @classmethod
    def clean_permissions(
        cls,
        requestor: "User",
        group: models.Group,
        errors: Dict[str, List[ValidationError]],
        cleaned_input: dict,
    ):
        super().clean_permissions(requestor, group, errors, cleaned_input)
        field = "remove_permissions"
        permission_items = cleaned_input.get(field)
        if permission_items:
            cleaned_input[field] = get_permissions(permission_items)
            if not requestor.is_superuser:
                cls.ensure_can_manage_permissions(
                    requestor, errors, field, permission_items
                )
                cls.ensure_permissions_can_be_removed(errors, group, permission_items)

    @classmethod
    def ensure_permissions_can_be_removed(
        cls,
        errors: dict,
        group: models.Group,
        permissions: List["str"],
    ):
        missing_perms = get_not_manageable_permissions_after_removing_perms_from_group(
            group, permissions
        )
        if missing_perms:
            # add error
            permission_codes = [PermissionEnum.get(code) for code in permissions]
            msg = (
                "Permissions cannot be removed, "
                "some of permissions will not be manageable."
            )
            code = PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permission_codes}
            cls.update_errors(errors, msg, "remove_permissions", code, params)

    @classmethod
    def clean_users(
        cls,
        requestor: "User",
        errors: dict,
        cleaned_input: dict,
        group: models.Group,
    ):
        super().clean_users(requestor, errors, cleaned_input, group)
        remove_users = cleaned_input.get("remove_users")
        if remove_users:
            cls.ensure_can_manage_users(
                requestor, errors, "remove_users", cleaned_input
            )
            cls.clean_remove_users(requestor, errors, cleaned_input, group)

    @classmethod
    def ensure_can_manage_users(
        cls,
        requestor: "User",
        errors: Dict[str, List[ValidationError]],
        field: str,
        cleaned_input: dict,
    ):
        """Check if requestor can manage users from input.

        Requestor cannot manage users with wider scope of permissions.
        """
        if requestor.is_superuser:
            return
        users = cleaned_input[field]
        out_of_scope_users = get_out_of_scope_users(requestor, users)
        if out_of_scope_users:
            # add error
            ids = [
                graphene.Node.to_global_id("User", user_instance.pk)
                for user_instance in out_of_scope_users
            ]
            error_msg = "You can't manage these users."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_USER.value
            params = {"users": ids}
            cls.update_errors(errors, error_msg, field, code, params)

    @classmethod
    def clean_remove_users(
        cls,
        requestor: "User",
        errors: dict,
        cleaned_input: dict,
        group: models.Group,
    ):
        cls.check_if_removing_user_last_group(requestor, errors, cleaned_input)
        cls.check_if_users_can_be_removed(requestor, errors, cleaned_input, group)

    @classmethod
    def check_if_removing_user_last_group(
        cls, requestor: "User", errors: dict, cleaned_input: dict
    ):
        """Ensure user doesn't remove user's last group."""
        remove_users = cleaned_input["remove_users"]
        if requestor in remove_users and requestor.groups.count() == 1:
            # add error
            error_msg = "You cannot remove yourself from your last group."
            code = PermissionGroupErrorCode.CANNOT_REMOVE_FROM_LAST_GROUP.value
            params = {"users": [graphene.Node.to_global_id("User", requestor.pk)]}
            cls.update_errors(errors, error_msg, "remove_users", code, params)

    @classmethod
    def check_if_users_can_be_removed(
        cls,
        requestor: "User",
        errors: dict,
        cleaned_input: dict,
        group: models.Group,
    ):
        """Check if after removing users from group all permissions will be manageable.

        After removing users from group, for each permission, there should be
        at least one staff member who can manage it (has both “manage staff”
        and this permission).
        """
        if requestor.is_superuser:
            return

        remove_users = cleaned_input["remove_users"]
        add_users = cleaned_input.get("add_users")
        manage_staff_permission = AccountPermissions.MANAGE_STAFF.value

        # check if user with manage staff will be added to the group
        if add_users:
            if any([user.has_perm(manage_staff_permission) for user in add_users]):
                return True

        permissions = get_not_manageable_permissions_after_removing_users_from_group(
            group, remove_users
        )
        if permissions:
            # add error
            permission_codes = [PermissionEnum.get(code) for code in permissions]
            msg = "Users cannot be removed, some of permissions will not be manageable."
            code = PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permission_codes}
            cls.update_errors(errors, msg, "remove_users", code, params)

    @classmethod
    def check_duplicates(
        cls,
        errors: dict,
        input_data: dict,
        fields: Tuple[str, str, str],
    ):
        """Check if any items are on both input field.

        Raise error if some of items are duplicated.
        """
        error = check_for_duplicates(input_data, *fields)
        if error:
            error.code = PermissionGroupErrorCode.DUPLICATED_INPUT_ITEM.value
            error_field = fields[2]
            errors[error_field].append(error)


class PermissionGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the group to delete.", required=True)

    class Meta:
        description = (
            "Delete permission group. Apps are not allowed to perform this mutation."
        )
        model = models.Group
        object_type = Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.permission_group_deleted, instance)

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        requestor = info.context.user
        if not requestor:
            raise PermissionDenied("You must be authenticated to perform this action.")
        if requestor.is_superuser:
            return
        if not can_user_manage_group(requestor, instance):
            error_msg = "You can't manage group with permissions out of your scope."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
            raise ValidationError(error_msg, code)

        cls.check_if_group_can_be_removed(requestor, instance)

    @classmethod
    def check_permissions(cls, context, permissions=None):
        app = get_app_promise(context).get()
        if app:
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)

    @classmethod
    def check_if_group_can_be_removed(cls, requestor, group):
        cls.ensure_deleting_not_left_not_manageable_permissions(group)
        cls.ensure_not_removing_requestor_last_group(group, requestor)

    @classmethod
    def ensure_deleting_not_left_not_manageable_permissions(cls, group):
        """Return true if management of all permissions is provided by other groups.

        After removing group, for each permission, there should be at least one staff
        member who can manage it (has both “manage staff” and this permission).
        """
        permissions = get_not_manageable_permissions_after_group_deleting(group)
        if permissions:
            permission_codes = [PermissionEnum.get(code) for code in permissions]
            msg = "Group cannot be removed, some of permissions will not be manageable."
            code = PermissionGroupErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permission_codes}
            raise ValidationError(
                {"id": ValidationError(message=msg, code=code, params=params)}
            )

    @classmethod
    def ensure_not_removing_requestor_last_group(cls, group, requestor):
        """Ensure user doesn't remove user's last group."""
        if requestor in group.user_set.all() and requestor.groups.count() == 1:
            msg = "You cannot delete your last group."
            code = PermissionGroupErrorCode.CANNOT_REMOVE_FROM_LAST_GROUP.value
            raise ValidationError({"id": ValidationError(message=msg, code=code)})
