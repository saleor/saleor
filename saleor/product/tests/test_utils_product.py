from datetime import datetime
from unittest.mock import patch

import pytz

from ..models import ProductChannelListing
from ..utils.product import mark_products_as_dirty


@patch("saleor.product.utils.product.ProductChannelListing.objects.filter")
def test_mark_products_as_dirty_skips_when_input_as_empty_dict(
    mocked_product_channel_listing_filter,
):
    # when
    mark_products_as_dirty({})

    # then
    assert not mocked_product_channel_listing_filter.called


def test_mark_products_as_dirty(product_list, channel_USD):
    # given
    product = product_list[0]
    product_channel_listing = product.channel_listings.all()
    product_channel_listing.update(discounted_price_dirty=False)

    assert ProductChannelListing.objects.count() != product_channel_listing.count()

    # when
    mark_products_as_dirty({channel_USD.id: {product.id}})

    # then
    assert product_channel_listing.filter(discounted_price_dirty=False).count() == 0
    assert (
        ProductChannelListing.objects.exclude(product_id=product.id)
        .filter(discounted_price_dirty=True)
        .count()
        == 0
    )


def test_mark_products_as_dirty_product_process_only_for_provided_channels(
    product_list, channel_PLN, channel_USD
):
    # given
    product = product_list[0]
    second_listing = product.channel_listings.create(
        channel=channel_PLN,
        discounted_price_amount=20,
        currency=channel_PLN.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=(datetime(1999, 1, 1, tzinfo=pytz.UTC)),
        discounted_price_dirty=False,
    )
    product_channel_listing = product.channel_listings.all()
    product_channel_listing.update(discounted_price_dirty=False)

    assert ProductChannelListing.objects.count() != product_channel_listing.count()

    # when
    mark_products_as_dirty({channel_USD.id: {product.id}})

    # then
    second_listing.refresh_from_db()
    assert second_listing.discounted_price_dirty is False
    assert (
        ProductChannelListing.objects.exclude(
            product_id=product.id, channel_id=channel_USD.id
        )
        .filter(discounted_price_dirty=True)
        .count()
        == 0
    )


def test_mark_products_as_dirty_product_process_with_multiple_products_and_channels(
    product_list, channel_PLN, channel_USD
):
    # given
    first_product = product_list[0]
    second_listing_for_first_product = first_product.channel_listings.create(
        channel=channel_PLN,
        discounted_price_amount=20,
        currency=channel_PLN.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=(datetime(1999, 1, 1, tzinfo=pytz.UTC)),
        discounted_price_dirty=False,
    )
    first_product_channel_listing = first_product.channel_listings.all()
    first_product_channel_listing.update(discounted_price_dirty=False)

    second_product = product_list[1]
    second_listing_for_second_product = second_product.channel_listings.create(
        channel=channel_PLN,
        discounted_price_amount=20,
        currency=channel_PLN.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=(datetime(1999, 1, 1, tzinfo=pytz.UTC)),
        discounted_price_dirty=False,
    )

    # when
    mark_products_as_dirty(
        {
            channel_USD.id: {first_product.id, second_product.id},
            channel_PLN.id: {first_product.id},
        }
    )

    # then
    second_listing_for_first_product.refresh_from_db()
    second_listing_for_second_product.refresh_from_db()
    assert second_listing_for_second_product.discounted_price_dirty is False
    listings_marked_as_dirty = ProductChannelListing.objects.filter(
        discounted_price_dirty=True
    )
    assert listings_marked_as_dirty.all().count() == 3
    assert listings_marked_as_dirty.filter(
        product_id=first_product.id, channel_id=channel_USD.id
    ).first()
    assert listings_marked_as_dirty.filter(
        product_id=first_product.id, channel_id=channel_PLN.id
    ).first()
    assert listings_marked_as_dirty.filter(
        product_id=second_product.id, channel_id=channel_USD.id
    ).first()
