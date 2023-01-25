from collections import defaultdict
from typing import List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....warehouse.error_codes import StockErrorCode
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.types import BulkStockError, NonNullList
from ...plugins.dataloaders import get_plugin_manager_promise
from ...warehouse.dataloaders import (
    StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader,
)
from ...warehouse.types import Warehouse
from ..mutations.product.product_create import StockInput
from ..types import ProductVariant
from ..utils import create_stocks


class ProductVariantStocksCreate(BaseMutation):
    product_variant = graphene.Field(
        ProductVariant, description="Updated product variant."
    )

    class Arguments:
        variant_id = graphene.ID(
            required=True,
            description="ID of a product variant for which stocks will be created.",
        )
        stocks = NonNullList(
            StockInput,
            required=True,
            description="Input list of stocks to create.",
        )

    class Meta:
        description = "Creates stocks for product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkStockError
        error_type_field = "bulk_stock_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        manager = get_plugin_manager_promise(info.context).get()
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)
        stocks = data["stocks"]
        variant = cls.get_node_or_error(
            info, data["variant_id"], only_type=ProductVariant
        )
        if stocks:
            warehouses = cls.clean_stocks_input(variant, stocks, errors)
            if errors:
                raise ValidationError(errors)
            new_stocks = create_stocks(variant, stocks, warehouses)

            for stock in new_stocks:
                transaction.on_commit(
                    lambda: manager.product_variant_back_in_stock(stock)
                )

        StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(
            info.context
        ).clear((variant.id, None, None))

        variant = ChannelContext(node=variant, channel_slug=None)
        return cls(product_variant=variant)

    @classmethod
    def clean_stocks_input(cls, variant, stocks_data, errors):
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]
        cls.check_for_duplicates(warehouse_ids, errors)
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        existing_stocks = variant.stocks.filter(warehouse__in=warehouses).values_list(
            "warehouse__pk", flat=True
        )
        error_msg = "Stock for this warehouse already exists for this product variant."
        indexes = []
        for warehouse_pk in existing_stocks:
            warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse_pk)
            indexes.extend(
                [i for i, id in enumerate(warehouse_ids) if id == warehouse_id]
            )
        cls.update_errors(
            errors, error_msg, "warehouse", StockErrorCode.UNIQUE, indexes
        )

        return warehouses

    @classmethod
    def check_for_duplicates(
        cls, warehouse_ids, errors: defaultdict[str, List[ValidationError]]
    ):
        duplicates = {id for id in warehouse_ids if warehouse_ids.count(id) > 1}
        error_msg = "Duplicated warehouse ID."
        indexes = []
        for duplicated_id in duplicates:
            indexes.append(
                [i for i, id in enumerate(warehouse_ids) if id == duplicated_id][-1]
            )
        cls.update_errors(
            errors, error_msg, "warehouse", StockErrorCode.UNIQUE, indexes
        )

    @classmethod
    def update_errors(
        cls, errors: defaultdict[str, List[ValidationError]], msg, field, code, indexes
    ):
        for index in indexes:
            error = ValidationError(msg, code=code, params={"index": index})
            errors[field].append(error)
