from typing import cast

from ....core.tracing import traced_atomic_transaction
from ....discount import models
from ....discount.utils import fetch_catalogue_info
from ....permission.enums import DiscountPermissions
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.types import DiscountError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Sale
from .sale_base_catalogue import SaleBaseCatalogueMutation
from .utils import convert_catalogue_info_to_global_ids


class SaleAddCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

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
