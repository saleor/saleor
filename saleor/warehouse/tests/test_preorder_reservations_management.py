from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from ...checkout.models import Checkout
from ...core.exceptions import InsufficientStock
from ...product.models import ProductVariantChannelListing
from ..models import PreorderAllocation, PreorderReservation
from ..reservations import reserve_preorders

COUNTRY_CODE = "US"
RESERVATION_LENGTH = 5


def test_reserve_preorders(checkout_line_with_preorder_item, channel_USD):
    checkout_line = checkout_line_with_preorder_item
    checkout_line.quantity = 5
    checkout_line.save()

    reserve_preorders(
        [checkout_line],
        [checkout_line.variant],
        COUNTRY_CODE,
        channel_USD.slug,
        timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
    )

    reservation = PreorderReservation.objects.get(checkout_line=checkout_line)
    assert reservation.quantity_reserved == 5
    assert reservation.reserved_until > timezone.now() + timedelta(minutes=1)


def test_preorder_reservation_skips_prev_reservation_delete_if_replace_is_disabled(
    checkout_line_with_preorder_item, assert_num_queries, channel_USD
):
    checkout_line = checkout_line_with_preorder_item

    with assert_num_queries(3):
        reserve_preorders(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD.slug,
            timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
            replace=False,
        )

    with assert_num_queries(4):
        reserve_preorders(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD.slug,
            timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
        )


def test_preorder_reservation_removes_previous_reservations_for_checkout(
    checkout_line_with_preorder_item, channel_USD
):
    checkout_line = checkout_line_with_preorder_item
    checkout_line.quantity = 5
    checkout_line.save()

    previous_reservation = PreorderReservation.objects.create(
        checkout_line=checkout_line,
        product_variant_channel_listing=checkout_line.variant.channel_listings.first(),
        quantity_reserved=5,
        reserved_until=timezone.now() + timedelta(hours=1),
    )

    reserve_preorders(
        [checkout_line],
        [checkout_line.variant],
        COUNTRY_CODE,
        channel_USD.slug,
        timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
    )

    with pytest.raises(PreorderReservation.DoesNotExist):
        previous_reservation.refresh_from_db()


def test_preorder_reservation_fails_if_there_is_not_enough_channel_threshold_available(
    checkout_line_with_preorder_item, channel_USD
):
    checkout_line = checkout_line_with_preorder_item
    checkout_line.quantity = 5
    checkout_line.save()

    channel_listing = checkout_line.variant.channel_listings.first()
    channel_listing.preorder_quantity_threshold = 2
    channel_listing.save()

    with pytest.raises(InsufficientStock):
        reserve_preorders(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD.slug,
            timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
        )


def test_preorder_reservation_fails_if_channel_threshold_was_allocated(
    order_line,
    preorder_variant_channel_threshold,
    checkout_line_with_preorder_item,
    channel_USD,
):
    checkout_line = checkout_line_with_preorder_item
    checkout_line.quantity = 5
    checkout_line.save()

    channel_listing = checkout_line.variant.channel_listings.first()
    channel_listing.preorder_quantity_threshold = 7
    channel_listing.save()

    variant = preorder_variant_channel_threshold
    product_variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    PreorderAllocation.objects.create(
        order_line=order_line,
        product_variant_channel_listing=product_variant_channel_listing,
        quantity=order_line.quantity,
    )

    with pytest.raises(InsufficientStock):
        reserve_preorders(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD.slug,
            timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
        )


def test_preorder_reservation_fails_if_channel_threshold_was_reserved(
    order_line,
    preorder_variant_channel_threshold,
    checkout_line_with_preorder_item,
    channel_USD,
):
    checkout_line = checkout_line_with_preorder_item
    checkout_line.quantity = 5
    checkout_line.save()

    variant = preorder_variant_channel_threshold
    variant.preorder_global_threshold = 7
    variant.save()

    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=variant,
        quantity=3,
    )
    product_variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    PreorderReservation.objects.create(
        checkout_line=other_checkout_line,
        product_variant_channel_listing=product_variant_channel_listing,
        quantity_reserved=other_checkout_line.quantity,
        reserved_until=timezone.now() + timedelta(minutes=5),
    )

    with pytest.raises(InsufficientStock):
        reserve_preorders(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD.slug,
            timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
        )


def test_preorder_reservation_fails_if_global_threshold_was_allocated(
    order_line,
    preorder_variant_channel_threshold,
    checkout_line_with_preorder_item,
    channel_PLN,
    channel_USD,
):
    checkout_line = checkout_line_with_preorder_item
    checkout_line.quantity = 5
    checkout_line.save()

    variant = preorder_variant_channel_threshold
    variant.preorder_global_threshold = 7
    variant.save()

    product_variant_channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_PLN.currency_code,
        preorder_quantity_threshold=10,
    )

    PreorderAllocation.objects.create(
        order_line=order_line,
        product_variant_channel_listing=product_variant_channel_listing,
        quantity=order_line.quantity,
    )

    with pytest.raises(InsufficientStock):
        reserve_preorders(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD.slug,
            timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
        )


def test_preorder_reservation_fails_if_global_threshold_was_reserved(
    order_line,
    preorder_variant_channel_threshold,
    checkout_line_with_preorder_item,
    channel_PLN,
    channel_USD,
):
    checkout_line = checkout_line_with_preorder_item
    checkout_line.quantity = 5
    checkout_line.save()

    variant = preorder_variant_channel_threshold
    variant.preorder_global_threshold = 7
    variant.save()

    product_variant_channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_PLN.currency_code,
        preorder_quantity_threshold=10,
    )

    other_checkout = Checkout.objects.create(channel=channel_PLN, currency="PLN")
    other_checkout_line = other_checkout.lines.create(
        variant=variant,
        quantity=3,
    )
    PreorderReservation.objects.create(
        checkout_line=other_checkout_line,
        product_variant_channel_listing=product_variant_channel_listing,
        quantity_reserved=other_checkout_line.quantity,
        reserved_until=timezone.now() + timedelta(minutes=5),
    )

    with pytest.raises(InsufficientStock):
        reserve_preorders(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD.slug,
            timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
        )


def test_preorder_reservation_fails_if_there_is_not_enough_global_threshold_available(
    checkout_line_with_preorder_item, channel_USD
):
    checkout_line = checkout_line_with_preorder_item
    checkout_line.quantity = 5
    checkout_line.save()

    checkout_line.variant.preorder_global_threshold = 3
    checkout_line.variant.save()

    with pytest.raises(InsufficientStock):
        reserve_preorders(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD.slug,
            timezone.now() + timedelta(minutes=RESERVATION_LENGTH),
        )
