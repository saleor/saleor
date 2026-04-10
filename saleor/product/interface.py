from dataclasses import dataclass
from decimal import Decimal


@dataclass
class VariantDiscountedPriceChange:
    variant_id: int
    channel_slug: str
    previous_price_amount: Decimal
    new_price_amount: Decimal
    currency: str

    @property
    def pk(self) -> tuple[int, str]:
        """Required by deferred payload mechanism to group deliveries per object.

        Uses (variant_id, channel_slug) because the same variant can have
        separate price change events for different channels.
        """
        return (self.variant_id, self.channel_slug)
