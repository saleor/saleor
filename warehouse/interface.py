from dataclasses import dataclass


@dataclass
class VariantChannelStockInfo:
    variant_id: int
    channel_slug: str

    @property
    def pk(self) -> tuple[int, str]:
        """Required by deferred payload mechanism to group deliveries per object.

        Uses (variant_id, channel_slug) because the same variant can have
        separate stock-availability events per channel.
        """
        return (self.variant_id, self.channel_slug)
