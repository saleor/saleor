import graphene
from django.core.exceptions import ValidationError

from ....app import models
from ....app.actions import delete_app
from ....app.error_codes import AppErrorCode
from ....permission.enums import AppPermission
from ....webhook.event_types import WebhookEventAsyncType
from ...account.utils import can_manage_app
from ...core import ResolveInfo
from ...core.mutations import DeprecatedModelMutation
from ...core.types import AppError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context, requestor_is_superuser
from ..types import App


class AppDelete(DeprecatedModelMutation):
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
    def perform_mutation(cls, _root, info, /, **data):
        instance = cls.get_instance(info, **data)
        cls.clean_instance(info, instance)

        manager = get_plugin_manager_promise(info.context).get()
        delete_app(instance, manager)

        return cls.success_response(instance)
