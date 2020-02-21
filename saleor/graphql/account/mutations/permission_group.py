from typing import List

import graphene
from django.contrib.auth import models as auth_models
from django.core.exceptions import ValidationError

from ....account import models as account_models
from ....account.error_codes import AccountErrorCode
from ....core.permissions import AccountPermissions, get_permissions
from ...account.types import User
from ...core.enums import PermissionEnum
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types.common import AccountError
from ...core.utils import from_global_id_strict_type
from ..types import Group


class PermissionGroupCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Group name.", required=True)
    permissions = graphene.List(
        graphene.NonNull(PermissionEnum),
        description="List of permission code names to assign to this group.",
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
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            cleaned_input["permissions"] = get_permissions(cleaned_input["permissions"])
        return cleaned_input


class PermissionGroupInput(graphene.InputObjectType):
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
        input = PermissionGroupInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = "Update permission group."
        model = auth_models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = AccountError
        error_type_field = "account_errors"


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
