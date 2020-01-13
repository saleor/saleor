import graphene
from django.contrib.auth import models
from django.db import transaction

from ....core.permissions import AccountPermissions
from ...core.enums import PermissionEnum
from ...core.mutations import ModelMutation
from ...core.types.common import AccountError
from ..types import PermissionGroup


class PermissionGroupInput(graphene.InputObjectType):
    name = graphene.String(description="Group name.", required=True)
    permissions = graphene.List(
        graphene.NonNull(PermissionEnum),
        description="List of permission code names to assign to this group.",
        required=False,
    )


class PermissionGroupCreate(ModelMutation):
    group = graphene.Field(PermissionGroup, description="The newly created group.")

    class Arguments:
        input = PermissionGroupInput(
            description="Input fields to create permission group.", required=True
        )

    class Meta:
        description = "Create new permission group."
        model = models.Group
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    @transaction.atomic
    def perform_mutation(cls, _root, info, **data):
        success_response = super().perform_mutation(_root, info, **data)
        input_data = data["input"]
        permission_names = input_data.get("permissions", [])
        permission_codes = [name.split(".")[1] for name in permission_names]
        permissions = models.Permission.objects.filter(codename__in=permission_codes)
        instance = success_response.group
        instance.permissions.add(*list(permissions))
        return success_response
