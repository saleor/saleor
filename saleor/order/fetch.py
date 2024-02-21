from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional, cast
from uuid import UUID

from django.db.models import prefetch_related_objects

from ..channel.models import Channel
from ..discount import DiscountType
from ..discount.interface import VariantPromotionRuleInfo, fetch_variant_rules_info
from ..discount.models import OrderLineDiscount, Voucher
from ..payment.models import Payment
from ..product.models import (
    Collection,
    DigitalContent,
    Product,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ..tax.models import TaxClass
from .models import Order, OrderLine


@dataclass
class OrderInfo:
    order: "Order"
    customer_email: "str"
    channel: "Channel"
    payment: Optional["Payment"]
    lines_data: Iterable["OrderLineInfo"]


@dataclass
class OrderLineInfo:
    line: "OrderLine"
    quantity: int
    variant: Optional["ProductVariant"] = None
    is_digital: Optional[bool] = None
    digital_content: Optional["DigitalContent"] = None
    replace: bool = False
    warehouse_pk: Optional[UUID] = None
    line_discounts: Optional[Iterable["OrderLineDiscount"]] = None


def fetch_order_info(order: "Order") -> OrderInfo:
    order_lines_info = fetch_order_lines(order)
    order_data = OrderInfo(
        order=order,
        customer_email=order.get_customer_email(),
        channel=order.channel,
        payment=order.get_last_payment(),
        lines_data=order_lines_info,
    )
    return order_data


def fetch_order_lines(order: "Order") -> list[OrderLineInfo]:
    lines = order.lines.prefetch_related("variant__digital_content")
    lines_info = []
    for line in lines:
        is_digital = line.is_digital
        variant = line.variant
        lines_info.append(
            OrderLineInfo(
                line=line,
                quantity=line.quantity,
                is_digital=is_digital,
                variant=variant,
                digital_content=variant.digital_content
                if is_digital and variant
                else None,
            )
        )

    return lines_info


@dataclass
class DraftOrderLineInfo:
    line: "OrderLine"
    variant: "ProductVariant"
    channel_listing: "ProductVariantChannelListing"
    product: "Product"
    product_type: "ProductType"
    collections: list["Collection"]
    discounts: list["OrderLineDiscount"]
    rules_info: list["VariantPromotionRuleInfo"]
    channel: "Channel"
    tax_class: Optional["TaxClass"] = None
    voucher: Optional["Voucher"] = None
    should_refresh_discounts = False

    def get_promotion_discounts(self) -> list["OrderLineDiscount"]:
        return [
            discount
            for discount in self.discounts
            if discount.type in [DiscountType.PROMOTION, DiscountType.ORDER_PROMOTION]
        ]

    def get_catalogue_discounts(self) -> list["OrderLineDiscount"]:
        return [
            discount
            for discount in self.discounts
            if discount.type == DiscountType.PROMOTION
        ]


def fetch_draft_order_lines_info(
    order: "Order", lines: Optional[Iterable["OrderLine"]] = None
) -> list[DraftOrderLineInfo]:
    prefetch_related_fields = [
        # TODO zedzior check if all are needed
        "variant__product__collections",
        "variant__product__channel_listings__channel",
        "variant__product__product_type__tax_class__country_rates",
        "variant__product__tax_class__country_rates",
        "variant__channel_listings__channel",
        "variant__channel_listings__variantlistingpromotionrule__promotion_rule__promotion__translations",
        "variant__channel_listings__variantlistingpromotionrule__promotion_rule__translations",
        "discounts__promotion_rule__promotion",
    ]

    if lines is None:
        lines = list(order.lines.prefetch_related(*prefetch_related_fields))
    else:
        prefetch_related_objects(lines, *prefetch_related_fields)

    lines_info = []
    channel = order.channel
    for line in lines:
        variant = cast(ProductVariant, line.variant)
        variant_channel_listing = ProductVariantChannelListing.objects.filter(
            channel=channel, variant=variant
        ).first()
        if not variant_channel_listing:
            continue

        rules_info = (
            fetch_variant_rules_info(variant_channel_listing, order.language_code)
            if not line.is_gift
            else []
        )
        lines_info.append(
            DraftOrderLineInfo(
                line=line,
                variant=variant,
                channel_listing=variant_channel_listing,
                product=variant.product,
                product_type=variant.product.product_type,
                collections=list(variant.product.collections.all()),
                discounts=list(line.discounts.all()),
                rules_info=rules_info,
                channel=channel,
                tax_class=variant.product.tax_class,
            )
        )
    return lines_info
