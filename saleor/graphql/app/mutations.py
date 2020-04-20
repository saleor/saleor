import graphene

from ...app import models
from ...core.permissions import AppPermission, get_permissions
from ..core.enums import PermissionEnum
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import AppError
from ..meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
from .types import App, AppToken


class AppInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the app.")
    is_active = graphene.Boolean(description="Determine if this app should be enabled.")
    permissions = graphene.List(
        PermissionEnum,
        description="List of permission code names to assign to this app.",
    )


class AppTokenInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the token.", required=False)
    app = graphene.ID(description="ID of app.", required=True)


class AppTokenCreate(ModelMutation):
    auth_token = graphene.types.String(
        description="The newly created authentication token."
    )

    class Arguments:
        input = AppTokenInput(
            required=True, description="Fields required to create a new auth token."
        )

    class Meta:
        description = "Creates a new token."
        model = models.AppToken
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def get_type_for_model(cls):
        # Fixme this method can be deleted when we will drop support for ServiceAccount
        # Let's create ticket for this
        return AppToken

    @classmethod
    def perform_mutation(cls, root, info, **data):
        input_data = data.get("input", {})
        instance = cls.get_instance(info, **data)
        cleaned_input = cls.clean_input(info, instance, input_data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        response = cls.success_response(instance)
        response.auth_token = instance.auth_token
        return response


class AppTokenDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of an auth token to delete.", required=True)

    class Meta:
        description = "Deletes an authentication token assigned to app."
        model = models.AppToken
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def get_type_for_model(cls):
        return AppToken


class AppCreate(ModelMutation):
    auth_token = graphene.types.String(
        description="The newly created authentication token."
    )

    class Arguments:
        input = AppInput(
            required=True, description="Fields required to create a new app.",
        )

    class Meta:
        description = "Creates a new app."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def get_type_for_model(cls):
        return App

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data, input_cls)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        instance.tokens.create(name="Default")

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.auth_token = instance.tokens.get().auth_token
        return response


class AppUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of an app to update.", required=True)
        input = AppInput(
            required=True, description="Fields required to update an existing app.",
        )

    class Meta:
        description = "Updates an existing app."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def get_type_for_model(cls):
        return App

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data, input_cls)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            cleaned_input["permissions"] = get_permissions(cleaned_input["permissions"])
        return cleaned_input


class AppDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of an app to delete.", required=True)

    class Meta:
        description = "Deletes an app."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def get_type_for_model(cls):
        return App


class AppUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates private metadata for an app."
        permissions = (AppPermission.MANAGE_APPS,)
        model = models.App
        public = False
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def get_type_for_model(cls):
        return App


class AppClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clear private metadata for an app."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        public = False
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def get_type_for_model(cls):
        return App
