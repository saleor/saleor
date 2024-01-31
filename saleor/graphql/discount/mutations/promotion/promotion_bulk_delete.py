import graphene
from django.db.models import Exists, OuterRef, QuerySet

from .....discount import models
from .....discount.utils import get_channels_for_rules, get_current_products_for_rules
from .....permission.enums import DiscountPermissions
from .....product.utils.product import mark_products_for_recalculate_discounted_price
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
        product_ids, channel_ids = cls.get_product_and_channel_ids(queryset)
        promotions = [promotion for promotion in queryset]
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.PROMOTION_DELETED)
        for promotion in promotions:
            cls.call_event(manager.promotion_deleted, promotion, webhooks=webhooks)
        mark_products_for_recalculate_discounted_price(product_ids, channel_ids)

    @classmethod
    def get_product_and_channel_ids(cls, qs: QuerySet[models.Promotion]):
        rules = models.PromotionRule.objects.filter(
            Exists(qs.filter(id=OuterRef("promotion_id")))
        )
        products = get_current_products_for_rules(rules)
        channel_ids = get_channels_for_rules(rules).values_list("id", flat=True)

        return set(products.values_list("id", flat=True)), set(channel_ids)
