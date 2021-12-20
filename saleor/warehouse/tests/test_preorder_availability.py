from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from freezegun import freeze_time

from ...checkout.fetch import CheckoutLineInfo
from ...core.exceptions import InsufficientStock
from ..availability import (
    check_preorder_threshold_bulk,
    check_stock_and_preorder_quantity,
    check_stock_and_preorder_quantity_bulk,
)
from ..models import PreorderReservation


@patch("saleor.warehouse.availability.check_preorder_threshold_in_orders")
@patch("saleor.warehouse.availability.check_stock_quantity")
def test_check_stock_and_preorder_quantity(
    mock_check_stock_quantity,
    mock_check_preorder_threshold,
    variant,
    preorder_variant_channel_threshold,
    channel_USD,
):
    check_stock_and_preorder_quantity(variant, "US", channel_USD.slug, 1)
    mock_check_stock_quantity.assert_called_once()

    check_stock_and_preorder_quantity(
        preorder_variant_channel_threshold, "US", channel_USD.slug, 1
    )
    mock_check_preorder_threshold.assert_called_once()
    assert (
        mock_check_preorder_threshold.call_args[0][0]
        == preorder_variant_channel_threshold
    )

    assert mock_check_preorder_threshold.call_args[0][1] == 1


@patch("saleor.warehouse.availability.check_preorder_threshold_bulk")
@patch("saleor.warehouse.availability.check_stock_quantity_bulk")
def test_check_stock_and_preorder_quantity_bulk(
    mock_check_stock_quantity_bulk,
    mock_check_preorder_threshold_bulk,
    variant,
    preorder_variant_channel_threshold,
    preorder_variant_with_end_date,
    channel_USD,
):
    stock_variant_quantity = 2
    preorder_quantity = 1
    global_quantity_limit = 50

    with freeze_time(
        preorder_variant_with_end_date.preorder_end_date + timedelta(days=3)
    ):
        check_stock_and_preorder_quantity_bulk(
            [
                variant,
                preorder_variant_channel_threshold,
                preorder_variant_with_end_date,
            ],
            "US",
            [stock_variant_quantity, preorder_quantity, stock_variant_quantity],
            channel_USD.slug,
            global_quantity_limit=global_quantity_limit,
        )

    mock_check_stock_quantity_bulk.assert_called_once()
    assert mock_check_stock_quantity_bulk.call_args[0][0] == [
        variant,
        preorder_variant_with_end_date,
    ]
    assert mock_check_stock_quantity_bulk.call_args[0][2] == [
        stock_variant_quantity,
        stock_variant_quantity,
    ]

    mock_check_preorder_threshold_bulk.assert_called_once()
    assert mock_check_preorder_threshold_bulk.call_args[0][0] == [
        preorder_variant_channel_threshold
    ]
    assert mock_check_preorder_threshold_bulk.call_args[0][1] == [preorder_quantity]


def test_check_preorder_threshold_bulk_channel_threshold(
    preorder_variant_channel_threshold, channel_USD
):
    variant = preorder_variant_channel_threshold
    global_quantity_limit = 30
    # test it doesn't raise an error for available preorder variant
    channel_listings = variant.channel_listings.all()
    available_preorder_quantity = channel_listings.annotate(
        available_preorder_quantity=F("preorder_quantity_threshold")
        - Coalesce(Sum("preorder_allocations__quantity"), 0)
    )[0].available_preorder_quantity
    assert (
        check_preorder_threshold_bulk(
            [variant],
            [available_preorder_quantity],
            channel_USD.slug,
            global_quantity_limit,
        )
        is None
    )

    # test if it raises error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_preorder_threshold_bulk(
            [variant],
            [available_preorder_quantity + 1],
            channel_USD.slug,
            global_quantity_limit,
        )


def test_check_preorder_reserved_threshold_bulk_channel_threshold(
    checkout_line_with_reserved_preorder_item, channel_PLN, channel_USD
):
    variant = checkout_line_with_reserved_preorder_item.variant

    # test it doesn't raise an error for available preorder variant
    assert (
        check_preorder_threshold_bulk(
            [variant],
            [5],
            channel_USD.slug,
            existing_lines=[],
            check_reservations=True,
            global_quantity_limit=None,
        )
        is None
    )

    # test if it raises error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_preorder_threshold_bulk(
            [variant],
            [9],
            channel_USD.slug,
            existing_lines=[],
            check_reservations=True,
            global_quantity_limit=None,
        )

    # Check excludes given checkout lines reservations
    line = checkout_line_with_reserved_preorder_item
    check_preorder_threshold_bulk(
        [variant],
        [9],
        channel_USD.slug,
        existing_lines=[
            CheckoutLineInfo(
                line=line,
                channel_listing=line.variant.product.channel_listings.first(),
                collections=[],
                product=line.variant.product,
                variant=line.variant,
                product_type=line.variant.product.product_type,
            )
        ],
        check_reservations=True,
        global_quantity_limit=None,
    )

    # Check excludes expired reservations
    PreorderReservation.objects.update(
        reserved_until=timezone.now() - timedelta(minutes=1)
    )

    check_preorder_threshold_bulk(
        [variant],
        [9],
        channel_USD.slug,
        existing_lines=[],
        check_reservations=True,
        global_quantity_limit=None,
    )


def test_check_preorder_reserved_threshold_bulk_global_threshold(
    checkout_line_with_reserved_preorder_item, channel_PLN, channel_USD
):
    variant = checkout_line_with_reserved_preorder_item.variant
    variant.preorder_global_threshold = 3
    variant.save()

    # test it doesn't raise an error for available preorder variant
    assert (
        check_preorder_threshold_bulk(
            [variant],
            [1],
            channel_USD.slug,
            existing_lines=[],
            check_reservations=True,
            global_quantity_limit=None,
        )
        is None
    )

    # test if it raises error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_preorder_threshold_bulk(
            [variant],
            [2],
            channel_USD.slug,
            existing_lines=[],
            check_reservations=True,
            global_quantity_limit=None,
        )

    # Check excludes given checkout lines reservations
    line = checkout_line_with_reserved_preorder_item

    check_preorder_threshold_bulk(
        [variant],
        [3],
        channel_USD.slug,
        existing_lines=[
            CheckoutLineInfo(
                line=line,
                channel_listing=line.variant.product.channel_listings.first(),
                collections=[],
                product=line.variant.product,
                variant=line.variant,
                product_type=line.variant.product.product_type,
            )
        ],
        check_reservations=True,
        global_quantity_limit=None,
    )

    # Check excludes expired reservations
    PreorderReservation.objects.update(
        reserved_until=timezone.now() - timedelta(minutes=1)
    )

    check_preorder_threshold_bulk(
        [variant],
        [3],
        channel_USD.slug,
        existing_lines=[],
        check_reservations=True,
        global_quantity_limit=None,
    )


def test_check_preorder_threshold_bulk_global_threshold(
    preorder_variant_global_threshold, channel_USD
):
    variant = preorder_variant_global_threshold
    global_quantity_limit = 30
    channel_listings = variant.channel_listings.all()
    global_allocation = sum(
        channel_listings.annotate(
            allocated_preorder_quantity=Coalesce(
                Sum("preorder_allocations__quantity"), 0
            )
        ).values_list("allocated_preorder_quantity", flat=True)
    )
    available_preorder_quantity = variant.preorder_global_threshold - global_allocation

    # test it doesn't raise an error for available preorder variant
    assert (
        check_preorder_threshold_bulk(
            [variant],
            [available_preorder_quantity],
            channel_USD.slug,
            global_quantity_limit,
        )
        is None
    )

    # test if it raises error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_preorder_threshold_bulk(
            [variant],
            [available_preorder_quantity + 1],
            channel_USD.slug,
            global_quantity_limit,
        )


def test_check_preorder_threshold_bulk_global_and_channel_threshold(
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
    channel_USD,
    channel_PLN,
):
    variant = preorder_variant_global_and_channel_threshold
    global_quantity_limit = 30

    channel_listings = variant.channel_listings.all()
    channel_listings = channel_listings.annotate_preorder_quantity_allocated()
    channel_listing_USD = channel_listings.get(channel=channel_USD)
    channel_listing_PLN = channel_listings.get(channel=channel_PLN)

    assert (
        channel_listing_PLN.preorder_quantity_threshold
        - channel_listing_PLN.preorder_quantity_allocated
        < channel_listing_PLN.preorder_quantity_threshold
    )
    # Global availability is smaller than the channel_USD availability
    global_availability = variant.preorder_global_threshold - sum(
        channel_listing.preorder_quantity_allocated
        for channel_listing in channel_listings
    )
    channel_listing_USD_availability = (
        channel_listing_USD.preorder_quantity_threshold
        - channel_listing_USD.preorder_quantity_allocated
    )
    assert global_availability < channel_listing_USD_availability

    # test it doesn't raise any error if global limit is not exceeded
    assert (
        check_preorder_threshold_bulk(
            [variant], [global_availability], channel_USD.slug, global_quantity_limit
        )
        is None
    )

    # test if it raises error due to global limit check
    # although it's available for this specific channel
    with pytest.raises(InsufficientStock):
        check_preorder_threshold_bulk(
            [variant],
            [channel_listing_USD_availability],
            channel_USD.slug,
            global_quantity_limit,
        )
