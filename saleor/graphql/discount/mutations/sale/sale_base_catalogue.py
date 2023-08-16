import graphene

from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion
from .....product.tasks import update_products_discounted_prices_for_promotion_task
from ....core import ResolveInfo
from ....core.utils import from_global_id_or_error, raise_validation_error
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Sale
from ...utils import (
    convert_migrated_sale_predicate_to_catalogue_info,
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
    def get_instance(cls, _info: ResolveInfo, id):
        type, _id = from_global_id_or_error(id, raise_error=False)
        if type == "Promotion":
            raise_validation_error(
                field="id",
                message="Provided ID refers to Promotion model. "
                "Please use 'promotionRuleCreate' mutation instead.",
                code=DiscountErrorCode.INVALID.value,
            )
        object_id = cls.get_global_id_or_error(id, "Sale")
        return Promotion.objects.get(old_sale_id=object_id)

    @classmethod
    def post_save_actions(
        cls, info: ResolveInfo, promotion, previous_predicate, new_predicate
    ):
        previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
            previous_predicate
        )
        new_catalogue = convert_migrated_sale_predicate_to_catalogue_info(new_predicate)
        if previous_catalogue != new_catalogue:
            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(
                manager.sale_updated,
                promotion,
                previous_catalogue,
                new_catalogue,
            )

        previous_product_ids = get_product_ids_for_predicate(previous_predicate)
        new_product_ids = get_product_ids_for_predicate(new_predicate)

        if previous_product_ids != new_product_ids:
            product_ids = previous_product_ids | new_product_ids
            update_products_discounted_prices_for_promotion_task.delay(
                list(product_ids)
            )
