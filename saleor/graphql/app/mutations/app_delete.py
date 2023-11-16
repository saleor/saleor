import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....app import models
from ....app.error_codes import AppErrorCode
from ....permission.enums import AppPermission
from ....webhook.event_types import WebhookEventAsyncType
from ...account.utils import can_manage_app
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import AppError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context, requestor_is_superuser
from ..types import App


class AppDelete(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of an app to delete.", required=True)

    class Meta:
        description = "Deletes an app."
        model = models.App
        object_type = App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.APP_DELETED,
                description="An app was deleted.",
            ),
        ]

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        data["qs"] = models.App.objects.filter(removed_at__isnull=True)
        instance = super().get_instance(info, **data)
        return instance

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        requestor = get_user_or_app_from_context(info.context)
        if not requestor_is_superuser(requestor) and not can_manage_app(
            requestor, instance
        ):
            msg = "You can't delete this app."
            code = AppErrorCode.OUT_OF_SCOPE_APP.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.app_deleted, instance)

    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        instance = cls.get_instance(info, **data)
        cls.clean_instance(info, instance)

        instance.removed_at = timezone.now()
        instance.is_active = False
        instance.save(update_fields=["removed_at", "is_active"])

        cls.post_save_action(info, instance, {})
        return cls.success_response(instance)
