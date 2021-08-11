from ...discount import models
from ..channel import ChannelContext, ChannelQsContext
from .filters import filter_sale_search, filter_voucher_search


def resolve_voucher(id, channel):
    sale = models.Voucher.objects.filter(id=id).first()
    return ChannelContext(node=sale, channel_slug=channel) if sale else None


def resolve_vouchers(info, channel_slug, **kwargs) -> ChannelQsContext:
    qs = models.Voucher.objects.all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_voucher_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_sale(id, channel):
    sale = models.Sale.objects.filter(id=id).first()
    return ChannelContext(node=sale, channel_slug=channel) if sale else None


def resolve_sales(info, channel_slug, **kwargs) -> ChannelQsContext:
    qs = models.Sale.objects.all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_sale_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)
