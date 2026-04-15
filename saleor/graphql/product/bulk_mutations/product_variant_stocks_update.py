from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....core.utils.events import call_event
from ....permission.enums import ProductPermissions
from ....product import models
from ....warehouse import models as warehouse_models
from ....warehouse.management import stock_bulk_update
from ....warehouse.webhooks.stock_events import (
    trigger_product_variant_back_in_stock,
    trigger_product_variant_out_of_stock,
    trigger_product_variant_stocks_updated,
)
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.types import BulkStockError, NonNullList
from ...core.validators import validate_one_of_args_is_in_mutation
from ...utils import get_user_or_app_from_context
from ...warehouse.dataloaders import StocksByProductVariantIdLoader
from ...warehouse.types import Warehouse
from ..mutations.product.product_create import StockInput
from ..types import ProductVariant
from .product_variant_stocks_create import ProductVariantStocksCreate


class ProductVariantStocksUpdate(ProductVariantStocksCreate):
    class Meta:
        description = "Updates stocks for product variant."
        doc_category = DOC_CATEGORY_PRODUCTS
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
        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)
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

            requestor = get_user_or_app_from_context(info.context)
            cls.update_or_create_variant_stocks(variant, stocks, warehouses, requestor)

        StocksByProductVariantIdLoader(info.context).clear(variant.id)

        variant = ChannelContext(node=variant, channel_slug=None)
        return cls(product_variant=variant)

    @classmethod
    @traced_atomic_transaction()
    def update_or_create_variant_stocks(
        cls, variant, stocks_data, warehouses, requestor
    ):
        stocks = []
        webhooks_stock_in = get_webhooks_for_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK
        )
        webhooks_stock_out = get_webhooks_for_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK
        )
        webhooks_stock_update = get_webhooks_for_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED
        )
        for stock_data, warehouse in zip(stocks_data, warehouses, strict=False):
            stock, is_created = warehouse_models.Stock.objects.get_or_create(
                product_variant=variant, warehouse=warehouse
            )
            if is_created or (
                (stock.quantity - stock.quantity_allocated)
                <= 0
                < stock_data["quantity"]
            ):
                call_event(
                    trigger_product_variant_back_in_stock,
                    stock,
                    webhooks=webhooks_stock_in,
                    requestor=requestor,
                )

            if stock_data["quantity"] <= 0 or (
                stock_data["quantity"] - stock.quantity_allocated <= 0
            ):
                call_event(
                    trigger_product_variant_out_of_stock,
                    stock,
                    webhooks=webhooks_stock_out,
                    requestor=requestor,
                )

            stock.quantity = stock_data["quantity"]
            stocks.append(stock)
        call_event(
            trigger_product_variant_stocks_updated,
            stocks,
            webhooks=webhooks_stock_update,
            requestor=requestor,
        )

        stock_bulk_update(stocks, ["quantity"])
