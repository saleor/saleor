import graphene

from ....menu import models
from ....permission.enums import MenuPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.doc_category import DOC_CATEGORY_MENU
from ...core.mutations import DeprecatedModelMutation
from ...core.types import MenuError
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Menu


@doc(category=DOC_CATEGORY_MENU)
class MenuInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the menu.")
    slug = graphene.String(description="Slug of the menu.", required=False)


@doc(category=DOC_CATEGORY_MENU)
@webhook_events(async_events={WebhookEventAsyncType.MENU_UPDATED})
class MenuUpdate(DeprecatedModelMutation):
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

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.menu_updated, instance)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)
