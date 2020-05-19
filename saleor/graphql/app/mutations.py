import graphene
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from ...app import models
from ...app.error_codes import AppErrorCode
from ...app.tasks import install_app_task
from ...core import JobStatus
from ...core.permissions import AppPermission, get_permissions
from ..account.utils import can_manage_app
from ..core.enums import PermissionEnum
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import AppError
from ..utils import get_user_or_app_from_context, requestor_is_superuser
from .types import App, AppToken
from .utils import ensure_can_manage_permissions


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

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        app = cleaned_input.get("app")
        requestor = get_user_or_app_from_context(info.context)
        if not requestor_is_superuser(requestor) and not can_manage_app(requestor, app):
            msg = "You can't manage this app."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"app": ValidationError(msg, code=code)})
        return cleaned_input


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

    @classmethod
    def clean_instance(cls, info, instance):
        app = instance.app
        requestor = get_user_or_app_from_context(info.context)
        if not requestor_is_superuser(requestor) and not can_manage_app(requestor, app):
            msg = "You can't delete this app token."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"id": ValidationError(msg, code=code)})


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
            requestor = get_user_or_app_from_context(info.context)
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
            ensure_can_manage_permissions(requestor, permissions)
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
        requestor = get_user_or_app_from_context(info.context)
        if not requestor_is_superuser(requestor) and not can_manage_app(
            requestor, instance
        ):
            msg = "You can't manage this app."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

        # clean and prepare permissions
        if "permissions" in cleaned_input:
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
            ensure_can_manage_permissions(requestor, permissions)
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

    @classmethod
    def clean_instance(cls, info, instance):
        requestor = get_user_or_app_from_context(info.context)
        if not requestor_is_superuser(requestor) and not can_manage_app(
            requestor, instance
        ):
            msg = "You can't delete this app."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"id": ValidationError(msg, code=code)})


class AppDeleteFailedInstallation(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            description="ID of failed installation to delete.", required=True
        )

    class Meta:
        description = "Delete failed installation."
        model = models.AppInstallation
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        requestor = get_user_or_app_from_context(info.context)
        permissions = instance.permissions.all()
        if not requestor_is_superuser(requestor) and not requestor.has_perms(
            permissions
        ):
            msg = "You don't have enough permission to perform this action."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

        if instance.status != JobStatus.FAILED:
            msg = "Cannot delete installation with different status than failed."
            code = AppErrorCode.FORBIDDEN.value
            raise ValidationError({"id": ValidationError(msg, code=code)})


class AppRetryInstall(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of failed installation.", required=True)
        activate_after_installation = graphene.Boolean(
            default_value=True,
            required=False,
            description="Determine if app will be set active or not.",
        )

    class Meta:
        description = "Retry failed installation of new app."
        model = models.AppInstallation
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.status = JobStatus.PENDING
        instance.save()

    @classmethod
    def clean_instance(cls, info, instance):
        requestor = get_user_or_app_from_context(info.context)
        permissions = instance.permissions.all()
        if not requestor_is_superuser(requestor) and not requestor.has_perms(
            permissions
        ):
            msg = "You don't have enough permission to perform this action."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

        if instance.status != JobStatus.FAILED:
            msg = "Cannot retry installation with different status than failed."
            code = AppErrorCode.FORBIDDEN.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

    @classmethod
    def perform_mutation(cls, root, info, **data):
        activate_after_installation = data.get("activate_after_installation")
        app_installation = cls.get_instance(info, **data)
        cls.clean_instance(info, app_installation)

        cls.save(info, app_installation, cleaned_input=None)
        install_app_task.delay(app_installation.pk, activate_after_installation)
        return cls.success_response(app_installation)


class AppInstallInput(graphene.InputObjectType):
    app_name = graphene.String(description="Name of the app to install.")
    manifest_url = graphene.String(description="Url to app's manifest in JSON format.")
    activate_after_installation = graphene.Boolean(
        default_value=True,
        required=False,
        description="Determine if app will be set active or not.",
    )
    permissions = graphene.List(
        PermissionEnum,
        description="List of permission code names to assign to this app.",
    )


class AppInstall(ModelMutation):
    class Arguments:
        input = AppInstallInput(
            required=True, description="Fields required to install a new app.",
        )

    class Meta:
        description = "Install new app by using app manifest."
        model = models.AppInstallation
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def clean_manifest_url(self, url):
        url_validator = URLValidator()
        try:
            url_validator(url)
        except (ValidationError, AttributeError):
            msg = "Enter a valid URL."
            code = AppErrorCode.INVALID.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        manifest_url = data.get("manifest_url")
        cls.clean_manifest_url(manifest_url)

        cleaned_input = super().clean_input(info, instance, data, input_cls)

        # clean and prepare permissions
        if "permissions" in cleaned_input:
            requestor = get_user_or_app_from_context(info.context)
            permissions = cleaned_input.pop("permissions")
            cleaned_input["permissions"] = get_permissions(permissions)
            ensure_can_manage_permissions(requestor, permissions)
        return cleaned_input

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        activate_after_installation = cleaned_input["activate_after_installation"]
        install_app_task.delay(instance.pk, activate_after_installation)
