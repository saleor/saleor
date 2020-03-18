from collections import defaultdict
from typing import Dict, List, Optional

import graphene
from django.contrib.auth import models as auth_models
from django.core.exceptions import ValidationError
from django.db import transaction
from graphql_jwt.exceptions import PermissionDenied

from ....account import models as account_models
from ....account.error_codes import PermissionGroupErrorCode
from ....core.permissions import AccountPermissions, get_permissions
from ...account.types import User
from ...account.utils import can_user_manage_group, get_permissions_user_has_not
from ...core.enums import PermissionEnum
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types.common import AccountError, PermissionGroupError
from ...core.utils import from_global_id_strict_type
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
    def perform_mutation(cls, _root, info, **data):
        group = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, group, data)
        group = cls.construct_instance(group, cleaned_input)
        cls.clean_instance(info, group)
        cls.save(info, group, cleaned_input)
        cls._save_m2m(info, group, cleaned_input)
        group.user_set.add(*cleaned_input["users_pks"])
        return cls(group=group)

    @classmethod
    def clean_input(
        cls, info, instance, data,
    ):
        cleaned_input = super().clean_input(info, instance, data)
        errors = defaultdict(list)
        cls.clean_permissions(info, errors, "permissions", cleaned_input)
        cls.clean_users(errors, "users", cleaned_input)

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
        error_field: Optional[str] = None,
    ):
        if field in cleaned_input:
            permissions = get_permissions_user_has_not(
                info.context.user, cleaned_input[field]
            )
            if permissions:
                error_msg = "You can't add permission that you don't have."
                permission_enums = [PermissionEnum.get(perm) for perm in permissions]
                cls.update_errors(
                    errors,
                    error_msg,
                    field,
                    PermissionGroupErrorCode.NO_PERMISSION.value,
                    permission_enums,
                    error_field,
                )
            cleaned_input[field] = get_permissions(cleaned_input[field])

    @classmethod
    def clean_users(
        cls,
        errors: Dict[Optional[str], List[ValidationError]],
        field: str,
        cleaned_input: dict,
        error_field: Optional[str] = None,
    ):
        if field in cleaned_input:
            user_pks = cls.get_user_pks(cleaned_input, field)
            cls.check_if_users_are_staff(errors, field, user_pks, error_field)

            cleaned_input[f"{field}_pks"] = user_pks

    @classmethod
    def get_user_pks(cls, cleaned_input: dict, field: str):
        if field not in cleaned_input:
            return []

        user_ids: List[str] = cleaned_input[field]

        user_pks = [
            from_global_id_strict_type(user_id, only_type=User, field="id")
            for user_id in user_ids
        ]

        return user_pks

    @classmethod
    def check_if_users_are_staff(
        cls,
        errors: Dict[Optional[str], List[ValidationError]],
        field: str,
        user_pks: List[str],
        error_field: Optional[str] = None,
    ):
        non_staff_users = list(
            account_models.User.objects.filter(pk__in=user_pks)
            .filter(is_staff=False)
            .values_list("pk", flat=True)
        )
        if non_staff_users:
            ids = [graphene.Node.to_global_id("User", pk) for pk in non_staff_users]
            error_msg = "User must be staff member."
            cls.update_errors(
                errors,
                error_msg,
                field,
                PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.value,
                ids,
                error_field,
            )

    @classmethod
    def update_errors(
        cls,
        errors: Dict[Optional[str], List[ValidationError]],
        msg: str,
        field: Optional[str],
        code: str,
        values: list,
        error_field: Optional[str] = None,
    ):
        error_field = error_field or field
        error = ValidationError(
            message=msg, code=code, params={error_field: values}  # type: ignore
        )
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
    def perform_mutation(cls, _root, info, **data):
        group = cls.get_instance(info, **data)
        if not can_user_manage_group(info.context.user, group):
            raise PermissionDenied()
        data = data.get("input")
        cleaned_input = cls.clean_input(info, group, data)
        group = cls.construct_instance(group, cleaned_input)
        cls.clean_instance(info, group)
        cls.save(info, group, cleaned_input)
        cls.update_group_permissions_and_users(group, cleaned_input)
        return cls(group=group)

    @classmethod
    def update_group_permissions_and_users(
        cls, group: auth_models.Group, cleaned_input: dict
    ):
        if "add_users_pks" in cleaned_input:
            group.user_set.add(*cleaned_input["add_users_pks"])
        remove_users_pks = cls.get_user_pks(cleaned_input, "remove_users")
        group.user_set.remove(*remove_users_pks)

        if "add_permissions" in cleaned_input:
            group.permissions.add(*cleaned_input["add_permissions"])
        if "remove_perissions" in cleaned_input:
            remove_permissions = get_permissions(cleaned_input["remove_perissions"])
            group.permissions.remove(*remove_permissions)

    @classmethod
    def clean_input(
        cls, info, instance, data,
    ):
        cleaned_input = super().clean_input(info, instance, data)
        errors = defaultdict(list)
        for field in ["users", "permissions"]:
            cls.check_for_duplicates(errors, cleaned_input, field)

        cls.clean_permissions(
            info, errors, "add_permissions", cleaned_input, "permissions"
        )
        cls.clean_users(errors, "add_users", cleaned_input, "users")

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def check_for_duplicates(
        cls,
        errors: Dict[Optional[str], List[ValidationError]],
        cleaned_input: dict,
        field: str,
    ):
        add_field = f"add_{field}"
        remove_field = f"remove_{field}"
        if add_field in cleaned_input and remove_field in cleaned_input:
            common_items = set(cleaned_input[add_field]) & set(
                cleaned_input[remove_field]
            )
            if common_items:
                if field == "permission":
                    values = [PermissionEnum.get(perm) for perm in common_items]
                else:
                    values = list(common_items)
                error_msg = (
                    "The same object cannot be in both list"
                    "for adding and removing items."
                )
                cls.update_errors(
                    errors,
                    error_msg,
                    None,
                    PermissionGroupErrorCode.CANNOT_ADD_AND_REMOVE.value,
                    values,
                    field,
                )


class PermissionGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the group to delete.", required=True)

    class Meta:
        description = "Delete permission group."
        model = auth_models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = AccountError
        error_type_field = "account_errors"
