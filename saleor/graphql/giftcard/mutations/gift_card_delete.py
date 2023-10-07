import graphene

from ....giftcard import models
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.mutations import ModelDeleteMutation
from ...core.types import GiftCardError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the gift card to delete.", required=True)

    class Meta:
        description = "Delete gift card." + ADDED_IN_31
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_DELETED,
                description="A gift card was deleted.",
            )
        ]

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.gift_card_deleted, instance)
