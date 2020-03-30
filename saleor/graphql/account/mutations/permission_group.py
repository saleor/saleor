from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import graphene
from django.contrib.auth import models as auth_models
from django.core.exceptions import ValidationError
from django.db import transaction

from ....account.error_codes import PermissionGroupErrorCode
from ....core.permissions import AccountPermissions, get_permissions
from ...account.utils import can_user_manage_group, get_out_of_scope_permissions
from ...core.enums import PermissionEnum
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types.common import PermissionGroupError
from ..types import Group


class PermissionGroupCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Group name.", required=True)
    permissions = graphene.List(
        graphene.NonNull(PermissionEnum),
        description="List of permission code names to assign to this group.",
        required=False,
    )
    users = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of users to assign to this group.",
        required=False,
    )


class PermissionGroupCreate(ModelMutation):
    group = graphene.Field(Group, description="The newly created group.")

    class Arguments:
        input = PermissionGroupCreateInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = "Create new permission group."
        model = auth_models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"

    @classmethod
    @transaction.atomic
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        users = cleaned_data.get("users")
        if users:
            instance.user_set.add(*users)

    @classmethod
    def clean_input(
        cls, info, instance, data,
    ):
        cleaned_input = super().clean_input(info, instance, data)
        errors = defaultdict(list)
        cls.clean_permissions(info, errors, "permissions", cleaned_input)
        user_items = cleaned_input.get("users")
        if user_items:
            cls.check_if_users_are_staff(errors, "users", cleaned_input)

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_permissions(
        cls,
        info,
        errors: Dict[Optional[str], List[ValidationError]],
        field: str,
        cleaned_input: dict,
    ):
        permission_items = cleaned_input.get(field)
        if permission_items:
            permissions = get_out_of_scope_permissions(
                info.context.user, cleaned_input[field]
            )
            if permissions:
                # add error
                error_msg = "You can't add permission that you don't have."
                code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
                params = {"permissions": permissions}
                cls.update_errors(errors, error_msg, field, code, params)

            cleaned_input[field] = get_permissions(cleaned_input[field])

    @classmethod
    def check_if_users_are_staff(
        cls,
        errors: Dict[Optional[str], List[ValidationError]],
        field: str,
        cleaned_input: dict,
    ):
        """Check if all of the users are staff members."""
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
        errors: Dict[Optional[str], List[ValidationError]],
        msg: str,
        field: Optional[str],
        code: str,
        params: dict,
    ):
        """Create ValidationError and add it to error list."""
        error = ValidationError(message=msg, code=code, params=params)
        errors[field].append(error)


class PermissionGroupUpdateInput(graphene.InputObjectType):
    name = graphene.String(description="Group name.", required=False)
    add_permissions = graphene.List(
        graphene.NonNull(PermissionEnum),
        description="List of permission code names to assign to this group.",
        required=False,
    )
    remove_permissions = graphene.List(
        graphene.NonNull(PermissionEnum),
        description="List of permission code names to unassign from this group.",
        required=False,
    )
    add_users = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of users to assign to this group.",
        required=False,
    )
    remove_users = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of users to unassign from this group.",
        required=False,
    )


class PermissionGroupUpdate(PermissionGroupCreate):
    group = graphene.Field(Group, description="Group which was edited.")

    class Arguments:
        id = graphene.ID(description="ID of the group to update.", required=True)
        input = PermissionGroupUpdateInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = "Update permission group."
        model = auth_models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"

    @classmethod
    @transaction.atomic
    def _save_m2m(cls, info, instance, cleaned_data):
        cls.update_group_permissions_and_users(instance, cleaned_data)

    @classmethod
    def update_group_permissions_and_users(
        cls, group: auth_models.Group, cleaned_input: dict
    ):
        add_users = cleaned_input.get("add_users")
        remove_users = cleaned_input.get("remove_users")
        if add_users:
            group.user_set.add(*add_users)
        if remove_users:
            group.user_set.remove(*remove_users)

        add_permissions = cleaned_input.get("add_permissions")
        remove_permissions = cleaned_input.get("remove_permissions")
        if add_permissions:
            group.permissions.add(*add_permissions)
        if remove_permissions:
            group.permissions.remove(*remove_permissions)

    @classmethod
    def clean_input(
        cls, info, instance, data,
    ):
        if not can_user_manage_group(info.context.user, instance):
            error_msg = "You can't manage group with permissions out of your scope."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
            raise ValidationError(error_msg, code)

        errors = defaultdict(list)
        permission_fields = ("add_permissions", "remove_permissions", "permissions")
        user_fields = ("add_users", "remove_users", "users")

        cls.check_for_duplicates(errors, data, permission_fields)
        cls.check_for_duplicates(errors, data, user_fields)

        cleaned_input = super().clean_input(info, instance, data)

        cls.clean_permissions(info, errors, "add_permissions", cleaned_input)
        remove_permissions = cleaned_input.get("remove_permissions")
        if remove_permissions:
            cleaned_input["remove_permissions"] = get_permissions(remove_permissions)
        cls.clean_users(info, errors, cleaned_input)

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_users(cls, info, errors: dict, cleaned_input: dict):
        remove_users = cleaned_input.get("remove_users")
        add_users = cleaned_input.get("add_users")
        if remove_users:
            cls.clean_remove_users(info, errors, cleaned_input)
        if add_users:
            cls.check_if_users_are_staff(errors, "add_users", cleaned_input)

    @classmethod
    def clean_remove_users(cls, info, errors, cleaned_input):
        """Ensure user doesn't remove user's last group."""
        user = info.context.user
        remove_users = cleaned_input["remove_users"]
        if user in remove_users and user.groups.count() == 1:
            # add error
            error_msg = "You cannot remove yourself from your last group."
            code = PermissionGroupErrorCode.CANNOT_REMOVE_FROM_LAST_GROUP.value
            params = {"users": [graphene.Node.to_global_id("User", user.pk)]}
            cls.update_errors(errors, error_msg, "remove_users", code, params)

    @classmethod
    def check_for_duplicates(
        cls, errors: dict, input_data: dict, fields: Tuple[str, str, str],
    ):
        """Check if any items are on both input field.

        Raise error if some of items are duplicated.
        """
        add_field, remove_field, error_class_field = fields
        # break if any of comparing field is not in input
        add_items = input_data.get(add_field)
        remove_items = input_data.get(remove_field)
        if not add_items or not remove_items:
            return

        common_items = set(input_data[add_field]) & set(input_data[remove_field])
        if common_items:
            # add error
            error_msg = (
                "The same object cannot be in both list"
                "for adding and removing items."
            )
            code = PermissionGroupErrorCode.CANNOT_ADD_AND_REMOVE.value
            params = {error_class_field: list(common_items)}
            cls.update_errors(errors, error_msg, None, code, params)


class PermissionGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the group to delete.", required=True)

    class Meta:
        description = "Delete permission group."
        model = auth_models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = PermissionGroupError
        error_type_field = "permission_group_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        if not can_user_manage_group(info.context.user, instance):
            error_msg = "You can't manage group with permissions out of your scope."
            code = PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.value
            raise ValidationError(error_msg, code)
