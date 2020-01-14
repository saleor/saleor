import graphene
from django.contrib.auth import models
from django.core.exceptions import ValidationError

from ....account.error_codes import AccountErrorCode
from ....core.permissions import AccountPermissions, get_permissions
from ...core.enums import PermissionEnum
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types.common import AccountError
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
        model = models.Group
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


class PermissionGroupUpdate(ModelMutation):
    group = graphene.Field(Group, description="Group which was edited.")

    class Arguments:
        id = graphene.ID(description="ID of the group to update.", required=True)
        input = PermissionGroupInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = "Update permission group."
        model = models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if "name" not in cleaned_input and "permissions" not in cleaned_input:
            raise ValidationError(
                {
                    "input": ValidationError(
                        "You must provide name or permissions to update.",
                        code=AccountErrorCode.REQUIRED,
                    )
                }
            )
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            cleaned_input["permissions"] = get_permissions(cleaned_input["permissions"])
        return cleaned_input


class PermissionGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the group to delete.", required=True)

    class Meta:
        description = "Delete permission group."
        model = models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = AccountError
        error_type_field = "account_errors"
