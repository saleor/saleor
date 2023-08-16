from typing import List, Optional

from .....core.tracing import traced_atomic_transaction
from .....discount.models import PromotionRule
from .....discount.sale_converter import create_catalogue_predicate
from .....graphql.channel import ChannelContext
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import DEPRECATED_IN_3X_MUTATION
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import DiscountError
from ....core.utils import WebhookEventInfo
from ...utils import subtract_migrated_sale_predicates
from .sale_base_catalogue import SaleBaseCatalogueMutation


class SaleRemoveCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = (
            "Removes products, categories, collections from a sale."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `promotionRuleUpdate` or `promotionRuleDelete` mutations instead."
        )
        doc_category = DOC_CATEGORY_DISCOUNTS
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.SALE_UPDATED,
                description="A sale was updated.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input
    ):
        promotion = cls.get_instance(info, id)
        rules = promotion.rules.all()
        previous_predicate = rules[0].catalogue_predicate

        with traced_atomic_transaction():
            new_predicate = cls.remove_items_from_predicate(
                rules, previous_predicate, input
            )
            if new_predicate:
                cls.post_save_actions(
                    info,
                    promotion,
                    previous_predicate,
                    new_predicate,
                )

        return SaleRemoveCatalogues(
            sale=ChannelContext(node=promotion, channel_slug=None)
        )

    @classmethod
    def remove_items_from_predicate(
        cls, rules: List[PromotionRule], previous_predicate: dict, input: dict
    ) -> Optional[dict]:
        catalogue_item_ids = cls.get_catalogue_item_ids(input)
        if any(catalogue_item_ids):
            predicate_to_remove = create_catalogue_predicate(*catalogue_item_ids)
            new_predicate = subtract_migrated_sale_predicates(
                previous_predicate, predicate_to_remove
            )
            for rule in rules:
                rule.catalogue_predicate = new_predicate
            PromotionRule.objects.bulk_update(rules, ["catalogue_predicate"])
            return new_predicate

        return None
