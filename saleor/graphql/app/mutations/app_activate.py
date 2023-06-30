import graphene

from ....app import models
from ....permission.enums import AppPermission
from ....webhook.event_types import WebhookEventAsyncType
from ...core.mutations import ModelMutation
from ...core.types import AppError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import App


class AppActivate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of app to activate.", required=True)

    class Meta:
        description = "Activate the app."
        model = models.App
        object_type = App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.APP_STATUS_CHANGED,
                description="An app was activated.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, _root, info, /, *, id):
        app = cls.get_instance(info, id=id)
        app.is_active = True
        cls.save(info, app, None)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.app_status_changed, app)
        return cls.success_response(app)
