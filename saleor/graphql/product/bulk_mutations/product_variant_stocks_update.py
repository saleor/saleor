from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....core.utils.events import call_event
from ....permission.enums import ProductPermissions
from ....product import models
from ....warehouse import models as warehouse_models
from ....warehouse.channel_stock_availability import (
    trigger_back_in_stock_in_channel_events_for_stocks,
    trigger_out_of_stock_in_channel_events_for_stocks,
)
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
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_one_of_args_is_in_mutation
from ...site.dataloaders import get_site_promise
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
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED,
                description="A product variant stock is updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK,
                description=(
                    "A product variant stock transitioned from no availability "
                    "to available quantity."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK,
                description=(
                    "A product variant stock transitioned from available "
                    "quantity to no availability."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_IN_CHANNEL,
                description=(
                    "A product variant is back in stock in a channel "
                    "(non click-and-collect warehouses)."
                    "\n\nNote: Triggered only when the "
                    "`useLegacyShippingZoneStockAvailability` shop setting is "
                    "disabled."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
                description=(
                    "A product variant is out of stock in a channel "
                    "(non click-and-collect warehouses)."
                    "\n\nNote: Triggered only when the "
                    "`useLegacyShippingZoneStockAvailability` shop setting is "
                    "disabled."
                ),
            ),
            WebhookEventInfo(
                type=(
                    WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_FOR_CLICK_AND_COLLECT
                ),
                description=(
                    "A product variant is back in stock in a channel "
                    "(click-and-collect warehouses)."
                    "\n\nNote: Triggered only when the "
                    "`useLegacyShippingZoneStockAvailability` shop setting is "
                    "disabled."
                ),
            ),
            WebhookEventInfo(
                type=(
                    WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_FOR_CLICK_AND_COLLECT
                ),
                description=(
                    "A product variant is out of stock in a channel "
                    "(click-and-collect warehouses)."
                    "\n\nNote: Triggered only when the "
                    "`useLegacyShippingZoneStockAvailability` shop setting is "
                    "disabled."
                ),
            ),
        ]

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

            site_settings = get_site_promise(info.context).get().settings
            requestor = get_user_or_app_from_context(info.context)
            cls.update_or_create_variant_stocks(
                variant, stocks, warehouses, site_settings, requestor
            )

        StocksByProductVariantIdLoader(info.context).clear(variant.id)

        variant = ChannelContext(node=variant, channel_slug=None)
        return cls(product_variant=variant)

    @classmethod
    @traced_atomic_transaction()
    def update_or_create_variant_stocks(
        cls, variant, stocks_data, warehouses, site_settings, requestor
    ):
        stocks = []
        back_in_stock_stocks: list[warehouse_models.Stock] = []
        out_of_stock_stocks: list[warehouse_models.Stock] = []
        webhooks_stock_in = get_webhooks_for_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK
        )
        webhooks_stock_out = get_webhooks_for_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK
        )
        webhooks_stock_update = get_webhooks_for_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED
        )
        use_legacy_stock_availability = (
            site_settings.use_legacy_shipping_zone_stock_availability
        )
        for stock_data, warehouse in zip(stocks_data, warehouses, strict=False):
            stock, is_created = warehouse_models.Stock.objects.get_or_create(
                product_variant=variant, warehouse=warehouse
            )
            old_available = stock.quantity - stock.quantity_allocated
            new_available = stock_data["quantity"] - stock.quantity_allocated

            if (is_created and new_available > 0) or (
                old_available <= 0 < new_available
            ):
                call_event(
                    trigger_product_variant_back_in_stock,
                    stock,
                    webhooks=webhooks_stock_in,
                    requestor=requestor,
                )
                back_in_stock_stocks.append(stock)

            if old_available > 0 >= new_available:
                call_event(
                    trigger_product_variant_out_of_stock,
                    stock,
                    webhooks=webhooks_stock_out,
                    requestor=requestor,
                )
                out_of_stock_stocks.append(stock)

            stock.quantity = stock_data["quantity"]
            stocks.append(stock)
        call_event(
            trigger_product_variant_stocks_updated,
            stocks,
            webhooks=webhooks_stock_update,
            requestor=requestor,
        )

        stock_bulk_update(stocks, ["quantity"])

        if not use_legacy_stock_availability:
            if back_in_stock_stocks:
                call_event(
                    trigger_back_in_stock_in_channel_events_for_stocks,
                    back_in_stock_stocks,
                    site_settings,
                )
            if out_of_stock_stocks:
                call_event(
                    trigger_out_of_stock_in_channel_events_for_stocks,
                    out_of_stock_stocks,
                    site_settings,
                )
