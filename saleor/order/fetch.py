from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional, cast
from uuid import UUID

from django.db.models import prefetch_related_objects

from ..channel.models import Channel
from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.pricing.interface import LineInfo
from ..core.taxes import zero_money
from ..discount import DiscountType, VoucherType
from ..discount.interface import (
    VariantPromotionRuleInfo,
    fetch_variant_rules_info,
    fetch_voucher_info,
)
from ..discount.models import OrderLineDiscount, Voucher
from ..discount.utils.voucher import (
    VoucherDenormalizedInfo,
    attach_voucher_to_line_info,
    get_the_cheapest_line,
)
from ..graphql.core.types import Money
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
    rules_info: list["VariantPromotionRuleInfo"] | None = None
    channel_listing: ProductVariantChannelListing | None = None
    voucher_denormalized_info: VoucherDenormalizedInfo | None = None

    @property
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
    order: "Order",
    lines: Iterable["OrderLine"] | None = None,
    fetch_actual_prices: bool = False,
) -> list[EditableOrderLineInfo]:
    """Fetch the necessary order lines info in order to recalculate its prices.

    `fetch_actual_prices` argument determines if the function should additionally
    retrieve the latest variant channel listing prices
    """
    prefetch_related_fields = [
        "discounts__promotion_rule__promotion",
        "variant__product__collections",
        "variant__product__product_type",
    ]
    if fetch_actual_prices:
        prefetch_related_fields.extend(
            [
                "variant__channel_listings__variantlistingpromotionrule__promotion_rule__promotion__translations",
                "variant__channel_listings__variantlistingpromotionrule__promotion_rule__translations",
            ]
        )

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

        variant_channel_listing = None
        rules_info = []
        if fetch_actual_prices:
            variant_channel_listing = _get_variant_listing(variant, channel.id)
            if variant_channel_listing:
                rules_info = (
                    fetch_variant_rules_info(
                        variant_channel_listing, order.language_code
                    )
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
                discounts=list(line.discounts.all()),
                channel=channel,
                voucher=None,
                voucher_code=None,
                voucher_denormalized_info=None,
                channel_listing=variant_channel_listing,
                rules_info=rules_info,
            )
        )

    attach_voucher_info(lines_info, order)

    return lines_info


def attach_voucher_info(lines_info: list[EditableOrderLineInfo], order: Order):
    """Collect necessary voucher info and attach it to order lines info."""
    voucher = order.voucher
    if voucher and (
        voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order
    ):
        voucher_info = fetch_voucher_info(voucher, order.voucher_code)
        attach_voucher_to_line_info(voucher_info, lines_info)
        denormalized_voucher_info = _fetch_denormalized_voucher_info(
            lines_info, voucher
        )
        _attach_denormalized_voucher_to_line_info(
            lines_info, denormalized_voucher_info, order.voucher_code
        )


def reattach_apply_once_per_order_voucher_info(
    lines_info: list[EditableOrderLineInfo],
    initial_cheapest_line_info: LineInfo | None,
    order: Order,
):
    """Reattach apply once per order voucher info if the cheapest line has changed."""
    if get_the_cheapest_line(lines_info) == initial_cheapest_line_info:
        return

    for line_info in lines_info:
        line_info.voucher = None
        line_info.voucher_code = None
        line_info.voucher_denormalized_info = None

    attach_voucher_info(lines_info, order)


def _get_variant_listing(
    variant: ProductVariant | None, channel_id: int
) -> ProductVariantChannelListing | None:
    if not variant:
        return None
    for channel_listing in variant.channel_listings.all():
        if channel_listing.channel_id == channel_id:
            return channel_listing
    return None


def _fetch_denormalized_voucher_info(
    lines_info: list[EditableOrderLineInfo], voucher: Voucher
):
    voucher_discounts = [
        discount
        for line_info in lines_info
        for discount in line_info.discounts
        if discount.voucher == voucher
    ]
    if not voucher_discounts:
        return None

    voucher_discount = voucher_discounts[0]
    return VoucherDenormalizedInfo(
        discount_value=voucher_discount.value,
        discount_value_type=voucher_discount.value_type,
        voucher_type=voucher.type,
        reason=voucher_discount.reason,
        name=voucher_discount.name,
        apply_once_per_order=voucher.apply_once_per_order,
        origin_line_ids=[
            discount.line_id for discount in voucher_discounts if discount.line_id
        ],
    )


def _attach_denormalized_voucher_to_line_info(
    lines_info: list[EditableOrderLineInfo],
    denormalized_voucher_info: VoucherDenormalizedInfo | None,
    voucher_code: str | None,
):
    if not denormalized_voucher_info:
        return

    # Denormalized vouchers of type SPECIFIC PRODUCT shouldn't be evaluated against
    # the latest eligible product catalog so it should be applied to the same lines
    # it originates from
    if denormalized_voucher_info.voucher_type == VoucherType.SPECIFIC_PRODUCT:
        discounted_lines_info = (
            line_info
            for line_info in lines_info
            if line_info.line.pk in denormalized_voucher_info.origin_line_ids
        )
        for line_info in discounted_lines_info:
            line_info.voucher_denormalized_info = denormalized_voucher_info
            line_info.voucher_code = voucher_code
        return

    # Denormalized voucher applicable once per order can be applied to the different
    # line than it originates from (it depends on the actual cheapest line)
    if denormalized_voucher_info.apply_once_per_order is True:
        if cheapest_line_info := get_the_cheapest_line(lines_info):
            cheapest_line_info = cast(EditableOrderLineInfo, cheapest_line_info)
            cheapest_line_info.voucher_denormalized_info = denormalized_voucher_info
            cheapest_line_info.voucher_code = voucher_code
        return
