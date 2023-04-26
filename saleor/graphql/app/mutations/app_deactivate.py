import graphene

from ....app import models
from ....app.events import app_event_deactivated
from ....permission.enums import AppPermission
from ...core.mutations import ModelMutation
from ...core.types import AppError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context
from ..types import App


class AppDeactivate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of app to deactivate.", required=True)

    class Meta:
        description = "Deactivate the app."
        model = models.App
        object_type = App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, info, /, *, id):
        requestor = get_user_or_app_from_context(info.context)
        app = cls.get_instance(info, id=id)
        app.is_active = False
        cls.save(info, app, None)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.app_status_changed, app)
        app_event_deactivated(app, requestor=requestor)
        return cls.success_response(app)
