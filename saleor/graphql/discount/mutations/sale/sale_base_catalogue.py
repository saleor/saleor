import copy

import graphene

from .....product.tasks import update_products_discounted_prices_for_promotion_task
from ....core import ResolveInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Sale
from ...utils import (
    convert_catalogue_info_into_predicate,
    get_product_ids_for_predicate,
)
from ..voucher.voucher_add_catalogues import CatalogueInput
from .sale_base_discount_catalogue import BaseDiscountCatalogueMutation


class SaleBaseCatalogueMutation(BaseDiscountCatalogueMutation):
    sale = graphene.Field(
        Sale, description="Sale of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale.")
        input = CatalogueInput(
            required=True,
            description="Fields required to modify catalogue IDs of sale.",
        )

    class Meta:
        abstract = True

    @classmethod
    def post_save_actions(
        cls, info: ResolveInfo, promotion, previous_catalogue, new_catalogue
    ):
        if previous_catalogue != new_catalogue:
            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(
                manager.sale_updated,
                promotion,
                previous_catalogue,
                new_catalogue,
            )

        previous_predicate = convert_catalogue_info_into_predicate(previous_catalogue)
        new_predicate = convert_catalogue_info_into_predicate(new_catalogue)
        previous_product_ids = get_product_ids_for_predicate(
            copy.deepcopy(previous_predicate)
        )
        new_product_ids = get_product_ids_for_predicate(copy.deepcopy(new_predicate))

        if previous_product_ids != new_product_ids:
            product_ids = previous_product_ids | new_product_ids
            update_products_discounted_prices_for_promotion_task.delay(
                list(product_ids)
            )
