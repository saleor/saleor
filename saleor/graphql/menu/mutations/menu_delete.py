import graphene

from ....menu import models
from ....permission.enums import MenuPermissions
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import MenuError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Menu


class MenuDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu to delete.")

    class Meta:
        description = "Deletes a menu."
        model = models.Menu
        object_type = Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.menu_deleted, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)
