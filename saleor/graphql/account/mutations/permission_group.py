from collections import defaultdict
from typing import List

import graphene
from django.contrib.auth import models as auth_models
from django.core.exceptions import ValidationError

from ....account import models as account_models
from ....account.error_codes import AccountErrorCode, PermissionGroupErrorCode
from ....core.permissions import AccountPermissions, get_permissions
from ...account.types import User
from ...account.utils import get_permissions_user_has_not
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
        cleaned_input, user_pks = cls.clean_input(info, group, data)
        group = cls.construct_instance(group, cleaned_input)
        cls.clean_instance(info, group)
        cls.save(info, group, cleaned_input)
        cls._save_m2m(info, group, cleaned_input)
        group.user_set.add(*user_pks)
        return cls(group=group)

    @classmethod
    def clean_input(
        cls, info, instance, data,
    ):
        cleaned_input = super().clean_input(info, instance, data)
        errors = defaultdict(list)
        cls.clean_permissions(info, errors, cleaned_input)
        user_pks = cls.clean_users(errors, cleaned_input)

        if errors:
            raise ValidationError(errors)

        return cleaned_input, user_pks

    @classmethod
    def clean_permissions(cls, info, errors, cleaned_input):
        if "permissions" in cleaned_input:
            permissions = get_permissions_user_has_not(
                info.context.user, cleaned_input["permissions"]
            )
            if permissions:
                error_msg = "You can't add permission that you don't have."
                permission_enums = [PermissionEnum.get(perm) for perm in permissions]
                cls.update_errors(
                    errors,
                    error_msg,
                    "permissions",
                    PermissionGroupErrorCode.NO_PERMISSION,
                    permission_enums,
                )
            cleaned_input["permissions"] = get_permissions(cleaned_input["permissions"])
        return cleaned_input

    @classmethod
    def clean_users(cls, errors, cleaned_input):
        if "users" in cleaned_input:
            user_pks = cls.prepare_user_pks(cleaned_input)
            cls.check_if_users_are_staff(errors, user_pks)
            return user_pks
        return []

    @classmethod
    def prepare_user_pks(cls, cleaned_input):
        user_ids: List[str] = cleaned_input["users"]

        user_pks = [
            from_global_id_strict_type(user_id, only_type=User, field="id")
            for user_id in user_ids
        ]

        return user_pks

    @classmethod
    def check_if_users_are_staff(cls, errors, user_pks: List[str]):
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
                "users",
                PermissionGroupErrorCode.ASSIGN_NON_STAFF_MEMBER.value,
                ids,
            )

    @classmethod
    def update_errors(cls, errors, msg, field, code, values):
        error = ValidationError(msg, code=code, params={field: values})
        errors[field].append(error)

    @classmethod
    def handle_typed_errors(cls, errors: list, **extra):
        typed_errors = [
            cls._meta.error_type_class(
                field=e.field,
                message=e.message,
                code=code,
                permissions=params.get("permissions") if params else None,
                users=params.get("users") if params else None,
            )
            for e, code, params in errors
        ]
        extra.update({cls._meta.error_type_field: typed_errors})
        return cls(errors=[e[0] for e in errors], **extra)


class PermissionGroupUpdateInput(graphene.InputObjectType):
    name = graphene.String(description="Group name.", required=False)
    permissions = graphene.List(
        graphene.NonNull(PermissionEnum),
        description="List of permission code names to assign to this group.",
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


class PermissionGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the group to delete.", required=True)

    class Meta:
        description = "Delete permission group."
        model = auth_models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = AccountError
        error_type_field = "account_errors"


class PermissionGroupAssignUsers(ModelMutation):
    group = graphene.Field(Group, description="Group to which users were assigned.")

    class Arguments:
        id = graphene.ID(
            description="ID of the group to which users will be assigned.",
            required=True,
        )
        users = graphene.List(
            graphene.NonNull(graphene.ID),
            description="List of users to assign to this group.",
            required=True,
        )

    class Meta:
        description = "Assign users to group."
        model = auth_models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        group = cls.get_instance(info, **data)
        user_pks = cls.prepare_user_pks(info, group, **data)
        cls.check_if_users_are_staff(user_pks)
        group.user_set.add(*user_pks)
        return cls(group=group)

    @classmethod
    def prepare_user_pks(cls, info, group, **data):
        cleaned_input = cls.clean_input(info, group, data, Group)
        user_ids: List[str] = cleaned_input["users"]

        user_pks = [
            from_global_id_strict_type(user_id, only_type=User, field="id")
            for user_id in user_ids
        ]

        return user_pks

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data, input_cls=input_cls)
        user_ids: List[str] = cleaned_input["users"]
        if not user_ids:
            raise ValidationError(
                {
                    "users": ValidationError(
                        "You must provide at least one staff user.",
                        code=AccountErrorCode.REQUIRED.value,
                    )
                }
            )
        return cleaned_input

    @staticmethod
    def check_if_users_are_staff(user_pks: List[int]):
        non_staff_users = account_models.User.objects.filter(pk__in=user_pks).filter(
            is_staff=False
        )
        if non_staff_users:
            raise ValidationError(
                {
                    "users": ValidationError(
                        "Some of users aren't staff members.",
                        code=AccountErrorCode.ASSIGN_NON_STAFF_MEMBER.value,
                    )
                }
            )


class PermissionGroupUnassignUsers(PermissionGroupAssignUsers):
    group = graphene.Field(Group, description="Group from which users were unassigned.")

    class Arguments:
        id = graphene.ID(
            description="ID of group from which users will be unassigned.",
            required=True,
        )
        users = graphene.List(
            graphene.NonNull(graphene.ID),
            description="List of users to assign to this group.",
            required=True,
        )

    class Meta:
        description = "Unassign users from group."
        model = auth_models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        group = cls.get_instance(info, **data)
        user_pks = cls.prepare_user_pks(info, group, **data)
        group.user_set.remove(*user_pks)
        return cls(group=group)
