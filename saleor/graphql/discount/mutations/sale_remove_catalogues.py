from typing import cast

from ....core.tracing import traced_atomic_transaction
from ....discount import models
from ....discount.utils import fetch_catalogue_info
from ....graphql.channel import ChannelContext
from ....permission.enums import DiscountPermissions
from ...core import ResolveInfo
from ...core.types import DiscountError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Sale
from .sale_base_catalogue import SaleBaseCatalogueMutation
from .utils import convert_catalogue_info_to_global_ids


class SaleRemoveCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = "Removes products, categories, collections from a sale."
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
            cls.remove_catalogues_from_node(sale, input)
            current_catalogue = fetch_catalogue_info(sale)
            cls.call_event(
                lambda: manager.sale_updated(
                    sale,
                    previous_catalogue=convert_catalogue_info_to_global_ids(
                        previous_catalogue
                    ),
                    current_catalogue=convert_catalogue_info_to_global_ids(
                        current_catalogue
                    ),
                )
            )

        return SaleRemoveCatalogues(sale=ChannelContext(node=sale, channel_slug=None))
