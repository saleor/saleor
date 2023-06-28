from typing import cast

from .....core.tracing import traced_atomic_transaction
from .....discount import models
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

            def sale_update_event():
                return manager.sale_updated(
                    sale,
                    previous_catalogue=previous_cat_converted,
                    current_catalogue=current_cat_converted,
                )

            cls.call_event(sale_update_event)

        return SaleAddCatalogues(sale=ChannelContext(node=sale, channel_slug=None))
