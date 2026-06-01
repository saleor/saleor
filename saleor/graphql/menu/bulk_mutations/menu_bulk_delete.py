import graphene
from django.conf import settings

from ....menu import models
from ....permission.enums import MenuPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import MenuError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Menu


class MenuBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description=(
                f"List of menu IDs to delete. The number of items is limited to {settings.BULK_DELETE_LIMIT} by default. "
                "Exceeding the limit returns an `INVALID` error."
            ),
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
        max_input_size = settings.BULK_DELETE_LIMIT

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        menus = list(queryset)
        queryset.delete()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.MENU_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for menu in menus:
            cls.call_event(manager.menu_deleted, menu, webhooks=webhooks)
