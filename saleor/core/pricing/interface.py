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
    voucher_code: str | None

    @property
    def variant_discounted_price(self):
        raise NotImplementedError

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

    def get_total_discount_amount(self) -> "Money":
        """Calculate the total discount amount from all applicable discounts.
        
        Returns the sum of all discount amounts for this line.
        """
        from ...core.taxes import zero_money
        
        if not self.discounts:
            currency = getattr(self.line, "currency", self.channel.currency_code)
            return zero_money(currency)
        
        # Get currency from first discount or line
        currency = getattr(
            next(iter(self.discounts), None), "currency", None
        ) or getattr(self.line, "currency", self.channel.currency_code)
        
        total_discount = zero_money(currency)
        for discount in self.discounts:
            discount_amount = getattr(discount, "amount", None)
            if discount_amount:
                total_discount += discount_amount
        
        return total_discount

    def get_best_discount(self) -> Optional[Union["OrderLineDiscount", "CheckoutLineDiscount"]]:
        """Get the discount with the highest amount.
        
        Returns the discount object with the maximum discount amount,
        or None if no discounts are available.
        """
        if not self.discounts:
            return None
        
        return max(
            self.discounts,
            key=lambda d: getattr(d, "amount_value", 0) or 0,
            default=None
        )

    def get_discount_summary(self) -> dict:
        """Get a summary of all discounts applied to this line.
        
        Returns a dictionary with discount counts and total amount.
        """
        promotion_count = len(self.get_promotion_discounts())
        voucher_count = len(self.get_voucher_discounts())
        total_amount = self.get_total_discount_amount()
        
        return {
            "total_discounts": len(list(self.discounts)),
            "promotion_discounts": promotion_count,
            "voucher_discounts": voucher_count,
            "total_amount": total_amount,
            "currency": total_amount.currency if total_amount else getattr(
                self.line, "currency", self.channel.currency_code
            ),
        }
