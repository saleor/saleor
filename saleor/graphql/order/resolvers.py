from typing import List

from ...channel.models import Channel
from ...core.tracing import traced_resolver
from ...order import OrderPaymentStatus, OrderStatus, models
from ...order.events import OrderEvents
from ...order.models import OrderEvent
from ...order.utils import sum_order_totals
from ...payment import ChargeStatus
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..utils.filters import filter_by_period

ORDER_SEARCH_FIELDS = ("id", "discount_name", "token", "user_email", "user__email")


def resolve_orders(_info, channel_slug, **_kwargs):
    qs = models.Order.objects.non_draft()
    if channel_slug:
        qs = qs.filter(channel__slug=str(channel_slug))
    return qs


def resolve_draft_orders(_info, **_kwargs):
    qs = models.Order.objects.drafts()
    return qs


@traced_resolver
def resolve_orders_total(_info, period, channel_slug):
    if channel_slug is None:
        channel_slug = get_default_channel_slug_or_graphql_error()
    channel = Channel.objects.filter(slug=str(channel_slug)).first()
    if not channel:
        return None
    qs = (
        models.Order.objects.non_draft()
        .exclude(status=OrderStatus.CANCELED)
        .filter(channel__slug=str(channel_slug))
    )
    qs = filter_by_period(qs, period, "created")
    return sum_order_totals(qs, channel.currency_code)


def resolve_order(id):
    return models.Order.objects.filter(pk=id).first()


def resolve_homepage_events():
    # Filter only selected events to be displayed on homepage.
    types = [
        OrderEvents.PLACED,
        OrderEvents.PLACED_FROM_DRAFT,
        OrderEvents.ORDER_FULLY_PAID,
    ]
    return OrderEvent.objects.filter(type__in=types)


def resolve_order_by_token(token):
    return (
        models.Order.objects.exclude(status=OrderStatus.DRAFT)
        .filter(token=token)
        .first()
    )


def resolve_order_payment_status(order: models.Order, payments: List[models.Payment]):
    def _map_payment_has_status(payments, status_list):
        return map(lambda p: p.charge_status in status_list, payments)

    if order.total_paid_amount > order.total_gross_amount:
        return OrderPaymentStatus.OVERPAID

    if order.total_paid_amount == order.total_gross_amount:
        return OrderPaymentStatus.FULLY_CHARGED

    if any(
        _map_payment_has_status(
            payments,
            [ChargeStatus.FULLY_REFUNDED, ChargeStatus.PARTIALLY_REFUNDED],
        )
    ):
        if all(_map_payment_has_status(payments, [ChargeStatus.FULLY_REFUNDED])):
            return OrderPaymentStatus.FULLY_REFUNDED
        return OrderPaymentStatus.PARTIALLY_REFUNDED

    if any(
        _map_payment_has_status(
            payments,
            [ChargeStatus.FULLY_CHARGED, ChargeStatus.PARTIALLY_CHARGED],
        )
    ):
        return OrderPaymentStatus.PARTIALLY_CHARGED

    return OrderPaymentStatus.NOT_CHARGED
