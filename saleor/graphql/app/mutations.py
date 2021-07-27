from collections import defaultdict
from typing import Dict, Iterable, List

import graphene
import requests
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat

from ...app import models
from ...app.error_codes import AppErrorCode
from ...app.installation_utils import REQUEST_TIMEOUT
from ...app.tasks import install_app_task
from ...app.validators import AppURLValidator
from ...core import JobStatus
from ...core.permissions import (
    AppPermission,
    get_permissions,
    get_permissions_enum_list,
    split_permission_codename,
)
from ..account.utils import can_manage_app
from ..core import types as grapqhl_types
from ..core.enums import PermissionEnum
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types.common import AppError
from ..utils import get_user_or_app_from_context, requestor_is_superuser
from .enums import AppExtensionTargetEnum, AppExtensionTypeEnum, AppExtensionViewEnum
from .types import App, AppToken, Manifest
from .utils import ensure_can_manage_permissions

T_ERRORS = Dict[str, List[ValidationError]]


class AppInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the app.")
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


class AppTokenVerify(BaseMutation):
    valid = graphene.Boolean(
        default_value=False,
        required=True,
        description="Determine if token is valid or not.",
    )

    class Arguments:
        token = graphene.String(description="App token to verify.", required=True)

    class Meta:
        description = "Verify provided app token."
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        token = data.get("token")
        app_token = models.AppToken.objects.filter(
            auth_token=token, app__is_active=True
        ).first()
        return AppTokenVerify(valid=bool(app_token))


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
            required=True,
            description="Fields required to update an existing app.",
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


class AppActivate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of app to activate.", required=True)

    class Meta:
        description = "Activate the app."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        app = cls.get_instance(info, **data)
        app.is_active = True
        cls.save(info, app, cleaned_input=None)
        return cls.success_response(app)


class AppDeactivate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of app to deactivate.", required=True)

    class Meta:
        description = "Deactivate the app."
        model = models.App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        app = cls.get_instance(info, **data)
        app.is_active = False
        cls.save(info, app, cleaned_input=None)
        return cls.success_response(app)


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
        if instance.status != JobStatus.FAILED:
            msg = "Cannot delete installation with different status than failed."
            code = AppErrorCode.INVALID_STATUS.value
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
        if instance.status != JobStatus.FAILED:
            msg = "Cannot retry installation with different status than failed."
            code = AppErrorCode.INVALID_STATUS.value
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
            required=True,
            description="Fields required to install a new app.",
        )

    class Meta:
        description = "Install new app by using app manifest."
        model = models.AppInstallation
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def clean_manifest_url(self, url):
        url_validator = AppURLValidator()
        try:
            url_validator(url)
        except (ValidationError, AttributeError):
            msg = "Enter a valid URL."
            code = AppErrorCode.INVALID_URL_FORMAT.value
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


class AppFetchManifest(BaseMutation):
    manifest = graphene.Field(Manifest)

    class Arguments:
        manifest_url = graphene.String(required=True)

    class Meta:
        description = "Fetch and validate manifest."
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(manifest=instance, errors=[])

    @classmethod
    def fetch_manifest(cls, manifest_url):
        try:
            response = requests.get(manifest_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            msg = "The request to fetch manifest data timed out."
            code = AppErrorCode.MANIFEST_URL_CANT_CONNECT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})
        except requests.HTTPError:
            msg = "Unable to fetch manifest data."
            code = AppErrorCode.MANIFEST_URL_CANT_CONNECT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})
        except ValueError:
            msg = "Incorrect structure of manifest."
            code = AppErrorCode.INVALID_MANIFEST_FORMAT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})
        except Exception:
            msg = "Can't fetch manifest data. Please try later."
            code = AppErrorCode.INVALID.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})

    @classmethod
    def _clean_app_url(cls, url):
        url_validator = AppURLValidator()
        url_validator(url)

    @classmethod
    def clean_manifest_url(cls, manifest_url):
        try:
            cls._clean_app_url(manifest_url)
        except (ValidationError, AttributeError):
            msg = "Enter a valid URL."
            code = AppErrorCode.INVALID_URL_FORMAT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        return Manifest(
            identifier=cleaned_data.get("id"),
            name=cleaned_data.get("name"),
            about=cleaned_data.get("about"),
            data_privacy=cleaned_data.get("dataPrivacy"),
            data_privacy_url=cleaned_data.get("dataPrivacyUrl"),
            homepage_url=cleaned_data.get("homepageUrl"),
            support_url=cleaned_data.get("supportUrl"),
            configuration_url=cleaned_data.get("configurationUrl"),
            app_url=cleaned_data.get("appUrl"),
            version=cleaned_data.get("version"),
            token_target_url=cleaned_data.get("tokenTargetUrl"),
            permissions=cleaned_data.get("permissions"),
            extensions=cleaned_data.get("extensions"),
        )

    @classmethod
    def clean_permissions(
        cls, required_permissions: List[str], saleor_permissions: Iterable[Permission]
    ) -> List[Permission]:
        missing_permissions = []
        all_permissions = {perm[0]: perm[1] for perm in get_permissions_enum_list()}
        for perm in required_permissions:
            if not all_permissions.get(perm):
                missing_permissions.append(perm)
        if missing_permissions:
            error_msg = "Given permissions don't exist."
            code = AppErrorCode.INVALID_PERMISSION.value
            params = {"permissions": missing_permissions}
            raise ValidationError(error_msg, code=code, params=params)

        permissions = [all_permissions[perm] for perm in required_permissions]
        permissions = split_permission_codename(permissions)
        return [p for p in saleor_permissions if p.codename in permissions]

    @classmethod
    def clean_manifest_data(cls, info, manifest_data):
        errors: T_ERRORS = defaultdict(list)

        cls.validate_required_fields(manifest_data, errors)

        saleor_permissions = get_permissions().annotate(
            formated_codename=Concat("content_type__app_label", Value("."), "codename")
        )
        try:
            app_permissions = cls.clean_permissions(
                manifest_data.get("permissions", []), saleor_permissions
            )
        except ValidationError as e:
            errors["permissions"].append(e)
            app_permissions = []

        manifest_data["permissions"] = [
            grapqhl_types.Permission(
                code=PermissionEnum.get(p.formated_codename), name=p.name
            )
            for p in app_permissions
        ]

        if not errors:
            cls.clean_extensions(manifest_data, app_permissions, errors)

        if errors:
            raise ValidationError(errors)

    @classmethod
    def _clean_extension_permissions(cls, extension, app_permissions, errors):
        permissions_data = extension.get("permissions", [])
        try:
            extension_permissions = cls.clean_permissions(
                permissions_data, app_permissions
            )
        except ValidationError as e:
            e.params["label"] = extension.get("label")
            errors["extensions"].append(e)
            return

        if len(extension_permissions) != len(permissions_data):
            errors["extensions"].append(
                ValidationError(
                    "Extension permission must be listed in App's permissions.",
                    code=AppErrorCode.OUT_OF_SCOPE_PERMISSION.value,
                )
            )

        extension["permissions"] = [
            grapqhl_types.Permission(
                code=PermissionEnum.get(p.formated_codename),
                name=p.name,
            )
            for p in extension_permissions
        ]

    @classmethod
    def clean_extensions(cls, manifest_data, app_permissions, errors):
        extensions = manifest_data.get("extensions", [])
        enum_map = [
            (AppExtensionViewEnum, "view"),
            (AppExtensionTypeEnum, "type"),
            (AppExtensionTargetEnum, "target"),
        ]
        for index, extension in enumerate(extensions):
            for enum, key in enum_map:
                try:
                    extension[key] = enum[extension[key]].value
                except KeyError:
                    errors["extensions"].append(
                        ValidationError(
                            f"Incorrect value for field: {key}",
                            code=AppErrorCode.INVALID.value,
                        )
                    )

            try:
                cls._clean_app_url(extension["url"])
            except (ValidationError, AttributeError):
                errors["extensions"].append(
                    ValidationError(
                        "Incorrect value for field: url.",
                        code=AppErrorCode.INVALID_URL_FORMAT.value,
                    )
                )

            cls._clean_extension_permissions(extension, app_permissions, errors)

    @classmethod
    def validate_required_fields(cls, manifest_data, errors):
        manifest_required_fields = {"id", "version", "name"}
        extension_required_fields = {
            "label",
            "url",
            "view",
            "type",
            "target",
        }
        manifest_missing_fields = manifest_required_fields.difference(manifest_data)
        if manifest_missing_fields:
            [
                errors[missing_field].append(
                    ValidationError("Field required.", code=AppErrorCode.REQUIRED.value)
                )
                for missing_field in manifest_missing_fields
            ]

        app_extensions_data = manifest_data.get("extensions", [])
        for extension in app_extensions_data:
            extension_fields = set(extension.keys())
            missing_fields = extension_required_fields.difference(extension_fields)
            if missing_fields:
                errors["extensions"].append(
                    ValidationError(
                        "Missing required fields for app extension: %s."
                        % ", ".join(missing_fields),
                        code=AppErrorCode.REQUIRED.value,
                    )
                )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        manifest_url = data.get("manifest_url")
        cls.clean_manifest_url(manifest_url)
        manifest_data = cls.fetch_manifest(manifest_url)
        cls.clean_manifest_data(info, manifest_data)

        instance = cls.construct_instance(instance=None, cleaned_data=manifest_data)
        return cls.success_response(instance)
