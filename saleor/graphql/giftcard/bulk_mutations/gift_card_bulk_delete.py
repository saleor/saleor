import graphene

from ....giftcard import models
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import GiftCardError, NonNullList
from ...directives import doc, webhook_events
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


@doc(category=DOC_CATEGORY_GIFT_CARDS)
@webhook_events(async_events={WebhookEventAsyncType.GIFT_CARD_DELETED})
class GiftCardBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of gift card IDs to delete."
        )

    class Meta:
        description = "Deletes gift cards."
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        instances = list(queryset)
        queryset.delete()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.GIFT_CARD_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for instance in instances:
            cls.call_event(manager.gift_card_deleted, instance, webhooks=webhooks)
