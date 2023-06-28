import graphene
from django.core.exceptions import ValidationError

from ....app import models
from ....app.error_codes import AppErrorCode
from ....permission.enums import AppPermission, get_permissions
from ....webhook.event_types import WebhookEventAsyncType
from ...account.utils import can_manage_app
from ...core.mutations import ModelMutation
from ...core.types import AppError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context, requestor_is_superuser
from ..types import App
from ..utils import ensure_can_manage_permissions
from .app_create import AppInput


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
        object_type = App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.APP_UPDATED,
                description="An app was updated.",
            ),
        ]

    @classmethod
    def clean_input(cls, info, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
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

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.app_updated, instance)
