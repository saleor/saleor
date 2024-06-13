from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.expressions import Exists, OuterRef
from django.utils import timezone

from ..checkout.error_codes import CheckoutErrorCode
from ..checkout.models import Checkout
from ..core.exceptions import GiftCardNotApplicable
from ..core.tracing import traced_atomic_transaction
from ..core.utils.events import call_event
from ..core.utils.promo_code import InvalidPromoCode, generate_promo_code
from ..order.actions import OrderFulfillmentLineInfo, create_fulfillments
from ..order.models import OrderLine
from ..site import GiftCardSettingsExpiryType
from . import GiftCardEvents, GiftCardLineData, events
from .models import GiftCard, GiftCardEvent
from .notifications import send_gift_card_notification

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ..account.models import User
    from ..app.models import App
    from ..order.models import Order
    from ..plugins.manager import PluginsManager
    from ..site.models import SiteSettings


def add_gift_card_code_to_checkout(
    checkout: Checkout, email: str, promo_code: str, currency: str
):
    """Add gift card data to checkout by code.

    Raise ValidationError if email is not provided.
    Raise InvalidPromoCode if gift card cannot be applied.
    """
    try:
        # only active gift card with currency the same as channel currency can be used
        gift_card = (
            GiftCard.objects.active(date=date.today())
            .filter(currency=currency)
            .get(code=promo_code)
        )
    except GiftCard.DoesNotExist:
        raise InvalidPromoCode()

    checkout.gift_cards.add(gift_card)
    checkout.save(update_fields=["last_change"])


def remove_gift_card_code_from_checkout_or_error(
    checkout: Checkout, gift_card_code: str
) -> None:
    """Remove gift card data from checkout by code or raise an error."""

    if gift_card := checkout.gift_cards.filter(code=gift_card_code).first():
        checkout.gift_cards.remove(gift_card)
        checkout.save(update_fields=["last_change"])
    else:
        raise ValidationError(
            "Cannot remove a gift card not attached to this checkout.",
            code=CheckoutErrorCode.INVALID.value,
        )


def deactivate_gift_card(gift_card: GiftCard):
    """Set gift card status as inactive."""
    if gift_card.is_active:
        gift_card.is_active = False
        gift_card.save(update_fields=["is_active"])


def activate_gift_card(gift_card: GiftCard):
    """Set gift card status as active."""
    if not gift_card.is_active:
        gift_card.is_active = True
        gift_card.save(update_fields=["is_active"])


def fulfill_non_shippable_gift_cards(
    order: "Order",
    order_lines: Iterable[OrderLine],
    settings: "SiteSettings",
    requestor_user: Optional["User"],
    app: Optional["App"],
    manager: "PluginsManager",
):
    gift_card_lines = get_non_shippable_gift_card_lines(order_lines)
    if not gift_card_lines:
        return
    fulfill_gift_card_lines(
        gift_card_lines, requestor_user, app, order, settings, manager
    )


def get_non_shippable_gift_card_lines(lines: Iterable[OrderLine]) -> "QuerySet":
    gift_card_lines = get_gift_card_lines(lines)
    non_shippable_lines = OrderLine.objects.filter(
        id__in=[line.pk for line in gift_card_lines], is_shipping_required=False
    )
    return non_shippable_lines


def get_gift_card_lines(lines: Iterable[OrderLine]):
    gift_card_lines = [line for line in lines if line.is_gift_card]
    return gift_card_lines


def fulfill_gift_card_lines(
    gift_card_lines: "QuerySet",
    requestor_user: Optional["User"],
    app: Optional["App"],
    order: "Order",
    settings: "SiteSettings",
    manager: "PluginsManager",
):
    lines_for_warehouses: defaultdict[UUID, list[OrderFulfillmentLineInfo]] = (
        defaultdict(list)
    )
    channel_slug = order.channel.slug
    for line in gift_card_lines.prefetch_related(
        "allocations__stock", "variant__stocks"
    ):
        if allocations := line.allocations.all():
            for allocation in allocations:
                quantity = allocation.quantity_allocated
                if quantity > 0:
                    warehouse_pk = allocation.stock.warehouse_id
                    lines_for_warehouses[warehouse_pk].append(
                        {"order_line": line, "quantity": quantity}
                    )
        else:
            stock = line.variant.stocks.for_channel_and_country(channel_slug).first()
            if not stock:
                raise GiftCardNotApplicable(
                    message="Lack of gift card stock for checkout channel.",
                )
            warehouse_pk = stock.warehouse_id
            lines_for_warehouses[warehouse_pk].append(
                {"order_line": line, "quantity": line.quantity}
            )

    return create_fulfillments(
        requestor_user,
        app,
        order,
        dict(lines_for_warehouses),
        manager,
        settings,
        notify_customer=True,
    )


@traced_atomic_transaction()
def gift_cards_create(
    order: "Order",
    gift_card_lines_info: Iterable["GiftCardLineData"],
    settings: "SiteSettings",
    requestor_user: Optional["User"],
    app: Optional["App"],
    manager: "PluginsManager",
):
    """Create purchased gift cards."""
    customer_user = order.user
    user_email = order.user_email
    gift_cards = []
    non_shippable_gift_cards = []
    expiry_date = calculate_expiry_date(settings)
    for line_data in gift_card_lines_info:
        order_line = line_data.order_line
        price = order_line.unit_price_gross
        line_gift_cards = [
            GiftCard(  # type: ignore[misc] # see below:
                code=generate_promo_code(),
                initial_balance=price,  # money field not supported by mypy_django_plugin # noqa: E501
                current_balance=price,  # money field not supported by mypy_django_plugin # noqa: E501
                created_by=customer_user,
                created_by_email=user_email,
                product=line_data.variant.product if line_data.variant else None,
                fulfillment_line=line_data.fulfillment_line,
                expiry_date=expiry_date,
            )
            for _ in range(line_data.quantity)
        ]
        gift_cards.extend(line_gift_cards)
        if not order_line.is_shipping_required:
            non_shippable_gift_cards.extend(line_gift_cards)

    gift_cards = GiftCard.objects.bulk_create(gift_cards)
    events.gift_cards_bought_event(gift_cards, order, requestor_user, app)

    for gift_card in gift_cards:
        call_event(manager.gift_card_created, gift_card)

    channel_slug = order.channel.slug
    # send to customer all non-shippable gift cards
    transaction.on_commit(
        lambda: send_gift_cards_to_customer(
            non_shippable_gift_cards,
            user_email,
            requestor_user,
            app,
            customer_user,
            manager,
            channel_slug,
        )
    )
    return gift_cards


def calculate_expiry_date(settings):
    """Calculate expiry date based on gift card settings."""
    today = timezone.now().date()
    expiry_date = None
    if settings.gift_card_expiry_type == GiftCardSettingsExpiryType.EXPIRY_PERIOD:
        expiry_period_type = settings.gift_card_expiry_period_type
        time_delta = {f"{expiry_period_type}s": settings.gift_card_expiry_period}
        expiry_date = today + relativedelta(**time_delta)
    return expiry_date


def send_gift_cards_to_customer(
    gift_cards: Iterable[GiftCard],
    user_email: str,
    requestor_user: Optional["User"],
    app: Optional["App"],
    customer_user: Optional["User"],
    manager: "PluginsManager",
    channel_slug: str,
):
    for gift_card in gift_cards:
        send_gift_card_notification(
            requestor_user,
            app,
            customer_user,
            user_email,
            gift_card,
            manager,
            channel_slug,
            resending=False,
        )


def deactivate_order_gift_cards(
    order_id: UUID, user: Optional["User"], app: Optional["App"]
):
    gift_card_events = GiftCardEvent.objects.filter(
        type=GiftCardEvents.BOUGHT, order_id=order_id
    )
    gift_cards = GiftCard.objects.filter(
        Exists(gift_card_events.filter(gift_card_id=OuterRef("id")))
    )
    gift_cards.update(is_active=False)
    events.gift_cards_deactivated_event(
        gift_cards.values_list("id", flat=True), user, app
    )


def order_has_gift_card_lines(order):
    return any(order.lines.filter(is_gift_card=True))


def assign_user_gift_cards(user):
    GiftCard.objects.filter(used_by_email=user.email).update(used_by=user)
    GiftCard.objects.filter(created_by_email=user.email).update(created_by=user)


def is_gift_card_expired(gift_card: GiftCard):
    """Return True when gift card expiry date pass."""
    today = timezone.now().date()
    return bool(gift_card.expiry_date) and gift_card.expiry_date < today  # type: ignore


def get_user_gift_cards(user: "User") -> "QuerySet":
    from django.db.models import Q

    return GiftCard.objects.filter(
        Q(used_by_email=user.email)
        | Q(created_by_email=user.email)
        | Q(used_by=user)
        | Q(created_by=user)
    )
