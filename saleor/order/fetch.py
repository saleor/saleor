from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from django.db.models import prefetch_related_objects

from ..channel.models import Channel
from ..core.db.connection import allow_writer
from ..core.pricing.interface import LineInfo
from ..discount import DiscountType, VoucherType
from ..discount.interface import (
    fetch_variant_rules_info,
    fetch_voucher_info,
)
from ..discount.models import OrderLineDiscount
from ..discount.utils.voucher import apply_voucher_to_line
from ..payment.models import Payment
from ..product.models import (
    DigitalContent,
    ProductVariant,
    ProductVariantChannelListing,
)
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
                digital_content=(
                    variant.digital_content if is_digital and variant else None
                ),
            )
        )

    return lines_info


@dataclass
class EditableOrderLineInfo(LineInfo):
    line: "OrderLine"
    discounts: list["OrderLineDiscount"]

    def get_manual_line_discount(
        self,
    ) -> Optional["OrderLineDiscount"]:
        for discount in self.discounts:
            if discount.type == DiscountType.MANUAL:
                return discount
        return None


def fetch_draft_order_lines_info(
    order: "Order", lines: Optional[Iterable["OrderLine"]] = None
) -> list[EditableOrderLineInfo]:
    prefetch_related_fields = [
        "discounts__promotion_rule__promotion",
        "variant__channel_listings__variantlistingpromotionrule__promotion_rule__promotion__translations",
        "variant__channel_listings__variantlistingpromotionrule__promotion_rule__translations",
        "variant__product__collections",
        "variant__product__product_type",
    ]
    if lines is None:
        with allow_writer():
            # TODO: load lines with dataloader and pass as an argument
            lines = list(order.lines.prefetch_related(*prefetch_related_fields))
    else:
        prefetch_related_objects(lines, *prefetch_related_fields)

    lines_info = []

    with allow_writer():
        # TODO: load channel with dataloader and pass as an argument
        channel = order.channel

    for line in lines:
        variant = line.variant
        if not variant:
            continue
        product = variant.product
        variant_channel_listing = get_prefetched_variant_listing(variant, channel.id)
        if not variant_channel_listing:
            continue

        rules_info = (
            fetch_variant_rules_info(variant_channel_listing, order.language_code)
            if not line.is_gift
            else []
        )
        lines_info.append(
            EditableOrderLineInfo(
                line=line,
                variant=variant,
                product=product,
                product_type=product.product_type,
                collections=list(product.collections.all()) if product else [],
                channel_listing=variant_channel_listing,
                discounts=list(line.discounts.all()),
                rules_info=rules_info,
                channel=channel,
                voucher=None,
                voucher_code=None,
            )
        )
    voucher = order.voucher
    if voucher and (
        voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order
    ):
        voucher_info = fetch_voucher_info(voucher, order.voucher_code)
        apply_voucher_to_line(voucher_info, lines_info)
    return lines_info


def get_prefetched_variant_listing(
    variant: Optional[ProductVariant], channel_id: int
) -> Optional[ProductVariantChannelListing]:
    if not variant:
        return None
    for channel_listing in variant.channel_listings.all():
        if channel_listing.channel_id == channel_id:
            return channel_listing
    return None
