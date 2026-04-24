import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....core.utils.events import call_event
from ....permission.enums import ProductPermissions
from ....product import models
from ....warehouse import models as warehouse_models
from ....warehouse.channel_stock_availability import (
    trigger_out_of_stock_in_channel_events_for_stocks,
)
from ....warehouse.management import delete_stocks
from ....warehouse.webhooks.stock_events import (
    trigger_product_variant_out_of_stock,
)
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, StockError
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_one_of_args_is_in_mutation
from ...site.dataloaders import get_site_promise
from ...utils import get_user_or_app_from_context
from ...warehouse.dataloaders import StocksByProductVariantIdLoader
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
        description = "Deletes stocks from product variant."
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = StockError
        error_type_field = "stock_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK,
                description=("A product variant stock is deleted from a warehouse."),
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

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        sku = data.get("sku")
        variant_id = data.get("variant_id")
        validate_one_of_args_is_in_mutation("sku", sku, "variant_id", variant_id)

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

        webhooks = get_webhooks_for_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK
        )
        stocks_to_delete_list = list(stocks_to_delete)
        requestor = get_user_or_app_from_context(info.context)
        for stock in stocks_to_delete_list:
            call_event(
                trigger_product_variant_out_of_stock,
                stock,
                webhooks=webhooks,
                requestor=requestor,
            )

        site_settings = get_site_promise(info.context).get().settings
        if not site_settings.use_legacy_shipping_zone_stock_availability:
            # Channel-event queries run on_commit after the deletion is applied,
            # but the in-memory stock objects are still safe to pass.
            call_event(
                trigger_out_of_stock_in_channel_events_for_stocks,
                stocks_to_delete_list,
                site_settings,
            )
        delete_stocks([stock.id for stock in stocks_to_delete_list])

        StocksByProductVariantIdLoader(info.context).clear(variant.id)

        variant = ChannelContext(node=variant, channel_slug=None)
        return cls(product_variant=variant)
