import datetime

import pytest
from django.utils import timezone

from ....plugins.manager import get_plugins_manager
from ....warehouse.models import PreorderReservation, Reservation
from ...fetch import fetch_checkout_info
from ...utils import add_variant_to_checkout


@pytest.fixture
def checkout_line(checkout_with_item):
    return checkout_with_item.lines.first()


@pytest.fixture
def checkout_lines(checkout_with_items):
    return checkout_with_items.lines.all()


@pytest.fixture
def checkout_line_with_reservation_in_many_stocks(
    customer_user, variant_with_many_stocks, checkout
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")
    checkout_line = checkout.lines.create(
        variant=variant,
        quantity=3,
        undiscounted_unit_price_amount=variant.channel_listings.get(
            channel_id=checkout.channel_id
        ).price_amount,
    )

    reserved_until = timezone.now() + datetime.timedelta(minutes=5)

    Reservation.objects.bulk_create(
        [
            Reservation(
                checkout_line=checkout_line,
                stock=stocks[0],
                quantity_reserved=2,
                reserved_until=reserved_until,
            ),
            Reservation(
                checkout_line=checkout_line,
                stock=stocks[1],
                quantity_reserved=1,
                reserved_until=reserved_until,
            ),
        ]
    )

    return checkout_line


@pytest.fixture
def checkout_line_with_one_reservation(
    customer_user, variant_with_many_stocks, checkout
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")
    checkout_line = checkout.lines.create(
        variant=variant,
        quantity=2,
        undiscounted_unit_price_amount=variant.channel_listings.get(
            channel_id=checkout.channel_id
        ).price_amount,
    )

    reserved_until = timezone.now() + datetime.timedelta(minutes=5)

    Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stocks[0],
        quantity_reserved=2,
        reserved_until=reserved_until,
    )

    return checkout_line


@pytest.fixture
def checkout_line_with_preorder_item(
    checkout, product, preorder_variant_channel_threshold
):
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 1)
    return checkout.lines.last()


@pytest.fixture
def checkout_line_with_reserved_preorder_item(
    checkout, product, preorder_variant_channel_threshold
):
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 2)
    checkout_line = checkout.lines.last()

    reserved_until = timezone.now() + datetime.timedelta(minutes=5)

    PreorderReservation.objects.create(
        checkout_line=checkout_line,
        product_variant_channel_listing=checkout_line.variant.channel_listings.first(),
        quantity_reserved=2,
        reserved_until=reserved_until,
    )

    return checkout_line
