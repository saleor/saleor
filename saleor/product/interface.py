from dataclasses import dataclass
from decimal import Decimal


@dataclass
class VariantDiscountedPriceChange:
    variant_id: int
    channel_id: int
    channel_slug: str
    previous_price_amount: Decimal
    new_price_amount: Decimal
    currency: str

    @property
    def pk(self) -> int:
        return self.variant_id
