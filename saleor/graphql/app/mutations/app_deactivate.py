import graphene

from ....app import models
from ....permission.enums import AppPermission
from ....webhook.event_types import WebhookEventAsyncType
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import DeprecatedModelMutation
from ...core.types import AppError
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import App


@doc(category=DOC_CATEGORY_APPS)
@webhook_events(async_events={WebhookEventAsyncType.APP_STATUS_CHANGED})
class AppDeactivate(DeprecatedModelMutation):
    """Deactivates an activate app."""

    class Arguments:
        id = graphene.ID(description="ID of app to deactivate.", required=True)

    class Meta:
        model = models.App
        object_type = App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, info, /, *, id):  # type: ignore[override]
        qs = models.App.objects.filter(removed_at__isnull=True)
        app = cls.get_instance(
            info,
            id=id,
            qs=qs,
        )
        app.is_active = False
        cls.save(info, app, None)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.app_status_changed, app)
        return cls.success_response(app)
