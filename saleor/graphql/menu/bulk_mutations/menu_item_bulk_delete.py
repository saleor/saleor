import graphene

from ....menu import models
from ....permission.enums import MenuPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import MenuError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import MenuItem


class MenuItemBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of menu item IDs to delete."
        )

    class Meta:
        description = "Deletes menu items."
        model = models.MenuItem
        object_type = MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.MENU_ITEM_DELETED,
                description="A menu item was deleted.",
            ),
        ]

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        menu_items = list(queryset)
        queryset.delete()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.MENU_ITEM_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for menu_item in menu_items:
            cls.call_event(manager.menu_item_deleted, menu_item, webhooks=webhooks)
