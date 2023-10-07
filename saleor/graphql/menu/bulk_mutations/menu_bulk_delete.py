import graphene

from ....menu import models
from ....permission.enums import MenuPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import MenuError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Menu


class MenuBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of menu IDs to delete."
        )

    class Meta:
        description = "Deletes menus."
        model = models.Menu
        object_type = Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)
        error_type_class = MenuError
        error_type_field = "menu_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.MENU_DELETED,
                description="A menu was deleted.",
            ),
        ]

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        menus = list(queryset)
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        for menu in menus:
            manager.menu_deleted(menu)
