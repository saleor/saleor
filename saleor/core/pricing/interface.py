from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Union

from ...discount import DiscountType

if TYPE_CHECKING:
    from prices import Money
    from ...channel.models import Channel
    from ...checkout.models import CheckoutLine
    from ...discount.models import CheckoutLineDiscount, OrderLineDiscount, Voucher
    from ...order.models import OrderLine
    from ...product.models import (
        Collection,
        Product,
        ProductType,
        ProductVariant,
    )


@dataclass
class LineInfo:
    line: Union["OrderLine", "CheckoutLine"]
    variant: Optional["ProductVariant"]
    product: Optional["Product"]
    product_type: Optional["ProductType"]
    collections: list["Collection"] = field(repr=False)
    channel: "Channel" = field(repr=False)
    discounts: Iterable[Union["OrderLineDiscount", "CheckoutLineDiscount"]]
    voucher: Optional["Voucher"]
    voucher_code: Optional[str]

    @property
    def variant_discounted_price(self) -> "Money":
        """Return the variant price discounted by catalogue promotion.
        
        This is a base implementation that calculates the discounted price
        by applying catalogue discounts to the undiscounted unit price.
        Subclasses may override this for more specific behavior.
        """
        from ...core.prices import quantize_price
        from ...core.taxes import zero_money
        from prices import Money

        # Get the undiscounted unit price from the line
        # CheckoutLine has undiscounted_unit_price, OrderLine has undiscounted_base_unit_price
        if hasattr(self.line, "undiscounted_unit_price"):
            undiscounted_price = self.line.undiscounted_unit_price
        elif hasattr(self.line, "undiscounted_base_unit_price"):
            undiscounted_price = self.line.undiscounted_base_unit_price
        else:
            # Fallback: try to get currency and use zero money
            currency = getattr(self.line, "currency", self.channel.currency_code)
            return zero_money(currency)

        # Apply catalogue discounts
        catalogue_discounts = self.get_catalogue_discounts()
        total_price = undiscounted_price * getattr(self.line, "quantity", 1)
        for discount in catalogue_discounts:
            total_price -= discount.amount

        # Calculate unit price, ensuring it's not negative
        quantity = getattr(self.line, "quantity", 1)
        currency = getattr(self.line, "currency", self.channel.currency_code)
        unit_price = max(total_price / quantity, zero_money(currency))
        return quantize_price(unit_price, currency)

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
