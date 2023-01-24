import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....product import models
from ....warehouse import models as warehouse_models
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, StockError
from ...core.validators import validate_one_of_args_is_in_mutation
from ...plugins.dataloaders import get_plugin_manager_promise
from ...warehouse.dataloaders import (
    StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader,
)
from ...warehouse.types import Warehouse
from ..types import ProductVariant


class ProductVariantStocksDelete(BaseMutation):
    product_variant = graphene.Field(
        ProductVariant, description="Updated product variant."
    )

    class Arguments:
        variant_id = graphene.ID(
            required=False,
            description="ID of product variant for which stocks will be deleted.",
        )
        sku = graphene.String(
            required=False,
            description="SKU of product variant for which stocks will be deleted.",
        )
        warehouse_ids = NonNullList(
            graphene.ID, description="Input list of warehouse IDs."
        )

    class Meta:
        description = "Delete stocks from product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = StockError
        error_type_field = "stock_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        sku = data.get("sku")
        variant_id = data.get("variant_id")
        validate_one_of_args_is_in_mutation("sku", sku, "variant_id", variant_id)

        manager = get_plugin_manager_promise(info.context).get()

        if variant_id:
            variant = cls.get_node_or_error(info, variant_id, only_type=ProductVariant)
        else:
            variant = models.ProductVariant.objects.filter(sku=sku).first()
            if not variant:
                raise ValidationError(
                    {
                        "sku": ValidationError(
                            f"Couldn't resolve to a node: {sku}", code="not_found"
                        )
                    }
                )

        warehouses_pks = cls.get_global_ids_or_error(
            data["warehouse_ids"], Warehouse, field="warehouse_ids"
        )
        stocks_to_delete = warehouse_models.Stock.objects.filter(
            product_variant=variant, warehouse__pk__in=warehouses_pks
        )

        for stock in stocks_to_delete:
            transaction.on_commit(lambda: manager.product_variant_out_of_stock(stock))

        stocks_to_delete.delete()

        StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(
            info.context
        ).clear((variant.id, None, None))

        variant = ChannelContext(node=variant, channel_slug=None)
        return cls(product_variant=variant)
