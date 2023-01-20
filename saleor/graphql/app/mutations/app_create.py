import graphene

from ....app import models
from ....permission.enums import AppPermission, get_permissions
from ...core.enums import PermissionEnum
from ...core.mutations import ModelMutation
from ...core.types import AppError, NonNullList
from ...decorators import staff_member_required
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context
from ..types import App
from ..utils import ensure_can_manage_permissions


class AppInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the app.")
    permissions = NonNullList(
        PermissionEnum,
        description="List of permission code names to assign to this app.",
    )


class AppCreate(ModelMutation):
    auth_token = graphene.types.String(
        description="The newly created authentication token."
    )

    class Arguments:
        input = AppInput(
            required=True,
            description="Fields required to create a new app.",
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Creates a new app. Requires the following "
            "permissions: AUTHENTICATED_STAFF_USER and MANAGE_APPS."
        )
        model = models.App
        object_type = App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def clean_input(cls, info, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            requestor = get_user_or_app_from_context(info.context)
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
            ensure_can_manage_permissions(requestor, permissions)
        return cleaned_input

    @classmethod
    @staff_member_required
    def perform_mutation(cls, _root, info, /, **data):
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        auth_token = cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        response = cls.success_response(instance)
        response.auth_token = auth_token
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.app_installed, instance)
        return response

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        _, auth_token = instance.tokens.create(name="Default")
        return auth_token
