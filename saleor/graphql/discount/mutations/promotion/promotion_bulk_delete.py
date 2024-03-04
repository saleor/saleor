import graphene
from django.db.models import Exists, OuterRef, QuerySet

from .....discount import models
from .....permission.enums import DiscountPermissions
from .....product.utils.product import (
    get_channel_to_products_map_from_rules,
    mark_products_in_channels_as_dirty,
)
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.utils import get_webhooks_for_event
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_317, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelBulkDeleteMutation
from ....core.types import DiscountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Promotion


class PromotionBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of promotion IDs to delete."
        )

    class Meta:
        description = "Deletes promotions." + ADDED_IN_317 + PREVIEW_FEATURE
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_DELETED,
                description="A promotion was deleted.",
            )
        ]

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        channel_to_products_map = cls.get_product_and_channel_map(queryset)
        promotions = [promotion for promotion in queryset]
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.PROMOTION_DELETED)
        for promotion in promotions:
            cls.call_event(manager.promotion_deleted, promotion, webhooks=webhooks)
        if channel_to_products_map:
            cls.call_event(mark_products_in_channels_as_dirty, channel_to_products_map)

    @classmethod
    def get_product_and_channel_map(cls, qs: QuerySet[models.Promotion]):
        rules = models.PromotionRule.objects.filter(
            Exists(qs.filter(id=OuterRef("promotion_id")))
        )
        channel_to_products_map = get_channel_to_products_map_from_rules(rules)

        return channel_to_products_map
