import graphene

from ....app import models
from ....core.permissions import AppPermission
from ...core.mutations import ModelMutation
from ...core.types import AppError
from ...plugins.dataloaders import load_plugin_manager
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

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        app = cls.get_instance(info, **data)
        app.is_active = True
        cls.save(info, app, cleaned_input=None)
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.app_status_changed, app)
        return cls.success_response(app)
