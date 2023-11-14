from ...discount import models
from ..channel import ChannelContext, ChannelQsContext
from ..core.context import get_database_connection_name
from .filters import filter_sale_search, filter_voucher_search


def resolve_voucher(info, id, channel):
    sale = (
        models.Voucher.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )
    return ChannelContext(node=sale, channel_slug=channel) if sale else None


def resolve_vouchers(info, channel_slug, **kwargs) -> ChannelQsContext:
    qs = models.Voucher.objects.using(get_database_connection_name(info.context)).all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_voucher_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_sale(info, id, channel):
    sale = (
        models.Sale.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )
    return ChannelContext(node=sale, channel_slug=channel) if sale else None


def resolve_sales(info, channel_slug, **kwargs) -> ChannelQsContext:
    qs = models.Sale.objects.using(get_database_connection_name(info.context)).all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_sale_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)
