from django.db.models import Exists, OuterRef, QuerySet

from ...channel.models import Channel
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
    promotion = (
        models.Promotion.objects.using(get_database_connection_name(info.context))
        .filter(old_sale_id=id)
        .first()
    )
    return ChannelContext(node=promotion, channel_slug=channel) if promotion else None


def resolve_sales(info, channel_slug, **kwargs) -> ChannelQsContext:
    connection_name = get_database_connection_name(info.context)
    qs = models.Promotion.objects.using(connection_name).filter(
        old_sale_id__isnull=False
    )
    if channel_slug:
        channel = Channel.objects.using(connection_name).filter(slug=channel_slug)
        rule_channel = models.PromotionRule.channels.through.objects.using(
            connection_name
        ).filter(channel__in=channel)
        rules = models.PromotionRule.objects.using(connection_name).filter(
            Exists(rule_channel.filter(promotionrule_id=OuterRef("id")))
        )
        qs = qs.filter(Exists(rules.filter(promotion_id=OuterRef("pk"))))

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_sale_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_promotion(info, id):
    return (
        models.Promotion.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )


def resolve_promotions(info) -> QuerySet:
    return models.Promotion.objects.using(
        get_database_connection_name(info.context)
    ).all()
