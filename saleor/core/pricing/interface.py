from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from ...discount import DiscountType

if TYPE_CHECKING:
    from ...channel.models import Channel
    from ...checkout.models import CheckoutLine
    from ...discount.interface import VariantPromotionRuleInfo
    from ...discount.models import CheckoutLineDiscount, OrderLineDiscount, Voucher
    from ...order.models import OrderLine
    from ...product.models import (
        Collection,
        Product,
        ProductType,
        ProductVariant,
        ProductVariantChannelListing,
    )


@dataclass
class LineInfo:
    line: Union["OrderLine", "CheckoutLine"]
    variant: Optional["ProductVariant"]
    product: Optional["Product"]
    product_type: Optional["ProductType"]
    collections: list["Collection"]
    channel_listing: "ProductVariantChannelListing"
    channel: "Channel"
    discounts: Iterable[Union["OrderLineDiscount", "CheckoutLineDiscount"]]
    rules_info: list["VariantPromotionRuleInfo"]
    voucher: Optional["Voucher"]
    voucher_code: Optional[str]

    def get_promotion_discounts(
        self,
    ):
        return [
            discount
            for discount in self.discounts
            if discount.type in [DiscountType.PROMOTION, DiscountType.ORDER_PROMOTION]
        ]

    def get_catalogue_discounts(
        self,
    ):
        return [
            discount
            for discount in self.discounts
            if discount.type == DiscountType.PROMOTION
        ]

    def get_voucher_discounts(
        self,
    ):
        return [
            discount
            for discount in self.discounts
            if discount.type == DiscountType.VOUCHER
        ]
