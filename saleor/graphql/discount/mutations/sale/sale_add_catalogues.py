from .....core.tracing import traced_atomic_transaction
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import DEPRECATED_IN_3X_MUTATION
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import DiscountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...utils import convert_migrated_sale_predicate_to_catalogue_info
from .sale_base_catalogue import SaleBaseCatalogueMutation


class SaleAddCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = (
            "Adds products, categories, collections to a sale."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `promotionRuleCreate` mutation instead."
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
        previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
            previous_predicate
        )
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            new_predicate = cls.add_items_to_predicate(rules, previous_predicate, input)
            current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
                new_predicate
            )

            cls.call_event(
                manager.sale_updated,
                promotion,
                previous_catalogue,
                current_catalogue,
            )

        return SaleAddCatalogues(sale=ChannelContext(node=promotion, channel_slug=None))
