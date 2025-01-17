from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property
from typing import Optional
from uuid import UUID

from django.db.models import prefetch_related_objects

from ..channel.models import Channel
from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.pricing.interface import LineInfo
from ..core.taxes import zero_money
from ..discount import DiscountType, VoucherType
from ..discount.interface import fetch_voucher_info
from ..discount.models import OrderLineDiscount
from ..discount.utils.voucher import apply_voucher_to_line
from ..graphql.core.types import Money
from ..payment.models import Payment
from ..product.models import DigitalContent, ProductVariant
from .models import Order, OrderLine


@dataclass
class OrderInfo:
    order: "Order"
    customer_email: "str"
    channel: "Channel"
    payment: Optional["Payment"]
    lines_data: list["OrderLineInfo"]


@dataclass
class OrderLineInfo:
    line: "OrderLine"
    quantity: int
    variant: Optional["ProductVariant"] = None
    is_digital: bool | None = None
    digital_content: Optional["DigitalContent"] = None
    replace: bool = False
    warehouse_pk: UUID | None = None
    line_discounts: Iterable["OrderLineDiscount"] | None = None


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

    @cached_property
    def variant_discounted_price(self) -> Money:
        """Return the variant price discounted by catalogue promotion."""
        catalogue_discounts = self.get_catalogue_discounts()
        total_price = self.line.undiscounted_base_unit_price * self.line.quantity
        for discount in catalogue_discounts:
            total_price -= discount.amount
        unit_price = max(
            total_price / self.line.quantity, zero_money(self.line.currency)
        )
        return quantize_price(unit_price, self.line.currency)

    def get_manual_line_discount(
        self,
    ) -> Optional["OrderLineDiscount"]:
        for discount in self.discounts:
            if discount.type == DiscountType.MANUAL:
                return discount
        return None


def fetch_draft_order_lines_info(
    order: "Order", lines: Iterable["OrderLine"] | None = None
) -> list[EditableOrderLineInfo]:
    prefetch_related_fields = [
        "discounts__promotion_rule__promotion",
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

        lines_info.append(
            EditableOrderLineInfo(
                line=line,
                variant=variant,
                product=product,
                product_type=product.product_type,
                collections=list(product.collections.all()) if product else [],
                discounts=list(line.discounts.all()),
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
