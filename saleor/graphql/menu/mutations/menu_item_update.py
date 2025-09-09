import graphene

from ....menu import models
from ....permission.enums import MenuPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_MENU
from ...core.types import MenuError
from ...core.utils import WebhookEventInfo
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import MenuItem
from .menu_item_create import MenuItemInput, MenuItemMutationBase


@doc(category=DOC_CATEGORY_MENU)
@webhook_events(async_events={WebhookEventAsyncType.MENU_ITEM_UPDATED})
class MenuItemUpdate(MenuItemMutationBase):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a menu item to update.")
        input = MenuItemInput(
            required=True,
            description=(
                "Fields required to update a menu item. Only one of `url`, `category`, "
                "`page`, `collection` is allowed per item."
            ),
        )

    class Meta:
        description = "Updates a menu item."
        model = models.MenuItem
        object_type = MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        # Only one item can be assigned per menu item
        instance.page = None
        instance.collection = None
        instance.category = None
        instance.url = None
        return super().construct_instance(instance, cleaned_data)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.menu_item_updated, instance)
