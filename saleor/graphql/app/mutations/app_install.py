import graphene
from django.core.exceptions import ValidationError
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import PydanticCustomError

from ....app import models
from ....app.error_codes import AppErrorCode
from ....app.tasks import install_app_task
from ....app.validators import AppURLValidator
from ....permission.enums import AppPermission, get_permissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.enums import PermissionEnum
from ...core.mutations import DeprecatedModelMutation
from ...core.types import AppError, BaseInputObjectType, NonNullList
from ...core.utils import WebhookEventInfo
from ...decorators import staff_member_required
from ...error import pydantic_to_validation_error
from ...utils import get_user_or_app_from_context
from ..types import AppInstallation
from ..utils import ensure_can_manage_permissions


class AppInstallInputSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    app_name: str | None = None
    manifest_url: str
    activate_after_installation: bool = True
    permissions: list = []

    @field_validator("manifest_url")
    @classmethod
    def validate_manifest_url(cls, v: str) -> str:
        url_validator = AppURLValidator()
        try:
            url_validator(v)
        except (ValidationError, AttributeError) as e:
            raise PydanticCustomError(
                AppErrorCode.INVALID_URL_FORMAT.value,
                "Enter a valid URL.",
                {"error_code": AppErrorCode.INVALID_URL_FORMAT.value},
            ) from e
        return v


class AppInstallInput(BaseInputObjectType):
    app_name = graphene.String(description="Name of the app to install.")
    manifest_url = graphene.String(description="URL to app's manifest in JSON format.")
    activate_after_installation = graphene.Boolean(
        default_value=True,
        required=False,
        description="Determine if app will be set active or not.",
    )
    permissions = NonNullList(
        PermissionEnum,
        description="List of permission code names to assign to this app.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_APPS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.APP_INSTALLED,
                description="An app was installed.",
            ),
        ]


class AppInstall(DeprecatedModelMutation):
    class Arguments:
        input = AppInstallInput(
            required=True,
            description="Fields required to install a new app.",
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Install new app by using app manifest. Requires the following "
            "permissions: AUTHENTICATED_STAFF_USER and MANAGE_APPS."
        )
        model = models.AppInstallation
        object_type = AppInstallation
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def clean_input(cls, info, instance, data, **kwargs):
        try:
            AppInstallInputSchema.model_validate(dict(data))
        except PydanticValidationError as exc:
            raise pydantic_to_validation_error(
                exc, default_error_code=AppErrorCode.INVALID.value
            ) from exc

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
    def perform_mutation(cls, root, info, /, **data):
        return super().perform_mutation(root, info, **data)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        activate_after_installation = cleaned_input["activate_after_installation"]
        install_app_task.delay(instance.pk, activate_after_installation)
