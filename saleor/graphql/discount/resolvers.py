from ...core.tracing import traced_resolver
from ...discount import models
from ..channel import ChannelQsContext


@traced_resolver
def resolve_vouchers(info, channel_slug, **_kwargs) -> ChannelQsContext:
    qs = models.Voucher.objects.all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


@traced_resolver
def resolve_sales(info, channel_slug, **_kwargs) -> ChannelQsContext:
    qs = models.Sale.objects.all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)
