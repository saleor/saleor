from typing import List, cast

from .....core.tracing import traced_atomic_transaction
from .....discount import models
from .....discount.models import Promotion, PromotionRule
from .....discount.sale_converter import create_catalogue_predicate_from_catalogue_data
from .....discount.utils import fetch_catalogue_info
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import DiscountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Sale
from ..utils import convert_catalogue_info_to_global_ids
from .sale_base_catalogue import SaleBaseCatalogueMutation


class SaleAddCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
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
        sale = cast(
            models.Sale,
            cls.get_node_or_error(info, id, only_type=Sale, field="sale_id"),
        )
        previous_catalogue = fetch_catalogue_info(sale)
        promotion = Promotion.objects.get(old_sale_id=sale.id)
        rules = promotion.rules.all()
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            cls.add_catalogues_to_node(sale, input)
            current_catalogue = fetch_catalogue_info(sale)
            previous_cat_converted = convert_catalogue_info_to_global_ids(
                previous_catalogue
            )
            current_cat_converted = convert_catalogue_info_to_global_ids(
                current_catalogue
            )
            cls.update_promotion_rules_predicate(rules, current_cat_converted)

            def sale_update_event():
                return manager.sale_updated(
                    sale,
                    previous_catalogue=previous_cat_converted,
                    current_catalogue=current_cat_converted,
                )

            cls.call_event(sale_update_event)

        return SaleAddCatalogues(sale=ChannelContext(node=sale, channel_slug=None))

    @classmethod
    def update_promotion_rules_predicate(cls, rules, new_catalogue):
        new_predicate = create_catalogue_predicate_from_catalogue_data(new_catalogue)
        for rule in rules:
            rule.catalogue_predicate = new_predicate
        PromotionRule.objects.bulk_update(rules, ["catalogue_predicate"])
