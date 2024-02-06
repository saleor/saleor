from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.db.models import prefetch_related_objects

from ..discount import DiscountType

if TYPE_CHECKING:
    from ..discount.interface import VariantPromotionRuleInfo
    from ..discount.models import Voucher
    from ..tax.models import TaxClass
    from ..channel.models import Channel
    from ..discount.models import OrderLineDiscount
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
    # product: "Product"
    # product_type: "ProductType"
    # collections: list["Collection"]
    discounts: list["OrderLineDiscount"]
    rules_info: list["VariantPromotionRuleInfo"]
    channel: "Channel"
    tax_class: Optional["TaxClass"] = None
    voucher: Optional["Voucher"] = None

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


def fetch_draft_order_lines(
    order: "Order", lines: list[Optional["OrderLine"]]
) -> list[DraftOrderLineInfo]:
    if lines is None:
        lines = list(order.lines.select_related("variant__product__product_type"))
    else:
        prefetch_related_objects(lines, "variant__product__product_type")
    lines = order.lines.prefetch_related("")
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
