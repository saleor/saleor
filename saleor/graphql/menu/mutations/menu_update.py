import graphene

from ....menu import models
from ....permission.enums import MenuPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import MenuError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Menu


class MenuInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu.")
    slug = graphene.String(description="Slug of the menu.", required=False)


class MenuUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu to update.")
        input = MenuInput(
            required=True, description="Fields required to update a menu."
        )

    class Meta:
        description = "Updates a menu."
        model = models.Menu
        object_type = Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.MENU_UPDATED,
                description="A menu was updated.",
            ),
        ]

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.menu_updated, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)
