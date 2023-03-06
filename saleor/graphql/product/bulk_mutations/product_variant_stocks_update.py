from collections import defaultdict
from typing import List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....product import models
from ....warehouse import models as warehouse_models
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.types import BulkStockError, NonNullList
from ...core.validators import validate_one_of_args_is_in_mutation
from ...plugins.dataloaders import get_plugin_manager_promise
from ...warehouse.dataloaders import (
    StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader,
)
from ...warehouse.types import Warehouse
from ..mutations.product.product_create import StockInput
from ..types import ProductVariant
from .product_variant_stocks_create import ProductVariantStocksCreate


class ProductVariantStocksUpdate(ProductVariantStocksCreate):
    class Meta:
        description = "Update stocks for product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkStockError
        error_type_field = "bulk_stock_errors"

    class Arguments:
        variant_id = graphene.ID(
            required=False,
            description="ID of a product variant for which stocks will be updated.",
        )
        sku = graphene.String(
            required=False,
            description="SKU of product variant for which stocks will be updated.",
        )
        stocks = NonNullList(
            StockInput,
            required=True,
            description="Input list of stocks to create or update.",
        )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)
        stocks = data["stocks"]
        sku = data.get("sku")
        variant_id = data.get("variant_id")

        validate_one_of_args_is_in_mutation("sku", sku, "variant_id", variant_id)

        if variant_id:
            variant = cls.get_node_or_error(info, variant_id, only_type=ProductVariant)
        if sku:
            variant = models.ProductVariant.objects.filter(sku=sku).first()
            if not variant:
                raise ValidationError(
                    {
                        "sku": ValidationError(
                            f"Couldn't resolve to a node: {sku}", code="not_found"
                        )
                    }
                )

        if stocks:
            warehouse_ids = [stock["warehouse"] for stock in stocks]
            cls.check_for_duplicates(warehouse_ids, errors)
            if errors:
                raise ValidationError(errors)
            warehouses = cls.get_nodes_or_error(
                warehouse_ids, "warehouse", only_type=Warehouse
            )

            manager = get_plugin_manager_promise(info.context).get()
            cls.update_or_create_variant_stocks(variant, stocks, warehouses, manager)

        StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(
            info.context
        ).clear((variant.id, None, None))

        variant = ChannelContext(node=variant, channel_slug=None)
        return cls(product_variant=variant)

    @classmethod
    @traced_atomic_transaction()
    def update_or_create_variant_stocks(cls, variant, stocks_data, warehouses, manager):
        stocks = []
        for stock_data, warehouse in zip(stocks_data, warehouses):
            stock, is_created = warehouse_models.Stock.objects.get_or_create(
                product_variant=variant, warehouse=warehouse
            )
            if is_created or (
                (stock.quantity - stock.quantity_allocated)
                <= 0
                < stock_data["quantity"]
            ):
                transaction.on_commit(
                    lambda: manager.product_variant_back_in_stock(stock)
                )

            if stock_data["quantity"] <= 0 or (
                stock_data["quantity"] - stock.quantity_allocated <= 0
            ):
                transaction.on_commit(
                    lambda: manager.product_variant_out_of_stock(stock)
                )

            stock.quantity = stock_data["quantity"]
            stocks.append(stock)
            transaction.on_commit(lambda: manager.product_variant_stock_updated(stock))

        warehouse_models.Stock.objects.bulk_update(stocks, ["quantity"])
