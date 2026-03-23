from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ChannelPriceChange:
    channel_id: int
    previous_price_amount: Decimal
    new_price_amount: Decimal
    currency: str


@dataclass
class VariantDiscountedPriceUpdatedInfo:
    variant_id: int
    changed_prices: list[ChannelPriceChange]
