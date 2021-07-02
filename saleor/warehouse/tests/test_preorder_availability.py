import pytest
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from ...core.exceptions import InsufficientStock
from ..availability import check_preorder_threshold_bulk


def test_check_preorder_threshold_bulk_channel_threshold(
    preorder_variant_channel_threshold, channel_USD
):

    variant = preorder_variant_channel_threshold
    # test it doesn't raise an error for available preorder variant
    channel_listings = variant.channel_listings.all()
    available_preorder_quantity = channel_listings.annotate(
        available_preorder_quantity=F("preorder_quantity_threshold")
        - Coalesce(Sum("preorder_allocations__quantity"), 0)
    )[0].available_preorder_quantity
    assert (
        check_preorder_threshold_bulk(
            [variant], [available_preorder_quantity], channel_USD.slug
        )
        is None
    )

    # test if it raises error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_preorder_threshold_bulk(
            [variant], [available_preorder_quantity + 1], channel_USD.slug
        )


def test_check_preorder_threshold_bulk_global_threshold(
    preorder_variant_global_threshold, channel_USD
):
    variant = preorder_variant_global_threshold
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
            [variant], [available_preorder_quantity], channel_USD.slug
        )
        is None
    )

    # test if it raises error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_preorder_threshold_bulk(
            [variant], [available_preorder_quantity + 1], channel_USD.slug
        )


def test_check_preorder_threshold_bulk_global_and_channel_threshold(
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
    channel_USD,
    channel_PLN,
):
    variant = preorder_variant_global_and_channel_threshold

    channel_listings = variant.channel_listings.all()
    channel_listings = channel_listings.annotate(
        available_preorder_quantity=F("preorder_quantity_threshold")
        - Coalesce(Sum("preorder_allocations__quantity"), 0),
        preorder_quantity_allocated=Coalesce(Sum("preorder_allocations__quantity"), 0),
    )
    channel_listing_USD = channel_listings.get(channel=channel_USD)
    channel_listing_PLN = channel_listings.get(channel=channel_PLN)

    assert (
        channel_listing_PLN.available_preorder_quantity
        < channel_listing_PLN.preorder_quantity_threshold
    )
    # Global availability is smaller than the channel_USD availability
    global_availability = variant.preorder_global_threshold - sum(
        channel_listing.preorder_quantity_allocated
        for channel_listing in channel_listings
    )
    assert global_availability < channel_listing_USD.available_preorder_quantity

    # test it doesn't raise any error if global limit is not exceeded
    assert (
        check_preorder_threshold_bulk(
            [variant], [global_availability], channel_USD.slug
        )
        is None
    )

    # test if it raises error due to global limit check
    # although it's available for this specific channel
    with pytest.raises(InsufficientStock):
        check_preorder_threshold_bulk(
            [variant],
            [channel_listing_USD.available_preorder_quantity],
            channel_USD.slug,
        )
