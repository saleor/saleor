import datetime
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ...attribute.models import AttributeValue
from ..models import (
    ProductChannelListing,
    VariantChannelListingPrice,
    VariantChannelListingPriceAttributeValue,
    VariantChannelListingPriceCustomerType,
)
from ..utils.window_prices import (
    find_window_price_rows_to_toggle,
    is_window_price_applicable,
    mark_products_dirty_for_listings,
    sync_window_price_rows,
)

NOW = datetime.datetime(2026, 10, 2, 12, tzinfo=datetime.UTC)
DAY = datetime.timedelta(days=1)


def _create_row(
    listing,
    *,
    valid_from=None,
    valid_to=None,
    is_applied=False,
    customer_type=None,
    value=None,
):
    row = VariantChannelListingPrice.objects.create(
        variant_channel_listing=listing,
        currency=listing.currency,
        price_amount=Decimal(5),
        valid_from=valid_from,
        valid_to=valid_to,
        is_applied=is_applied,
    )
    if customer_type is not None:
        VariantChannelListingPriceCustomerType.objects.create(
            listing_price=row, customer_type=customer_type
        )
    if value is not None:
        VariantChannelListingPriceAttributeValue.objects.create(
            listing_price=row, value=value
        )
    return row


@pytest.mark.parametrize(
    ("_case", "valid_from", "valid_to", "has_buyer_conditions", "expected"),
    [
        ("open window", NOW - DAY, NOW + DAY, False, True),
        ("open start only", NOW - DAY, None, False, True),
        ("open end only", None, NOW + DAY, False, True),
        ("starts now", NOW, NOW + DAY, False, True),
        ("ends now", NOW - DAY, NOW, False, False),
        ("future window", NOW + DAY, NOW + 2 * DAY, False, False),
        ("past window", NOW - 2 * DAY, NOW - DAY, False, False),
        ("no window", None, None, False, True),
        ("open window with buyer conditions", NOW - DAY, NOW + DAY, True, False),
    ],
)
def test_is_window_price_applicable(
    _case, valid_from, valid_to, has_buyer_conditions, expected
):
    # when
    applicable = is_window_price_applicable(
        valid_from, valid_to, has_buyer_conditions, NOW
    )

    # then
    assert applicable is expected


@pytest.mark.parametrize(
    ("_case", "valid_from", "valid_to", "is_applied", "conditioned", "expected"),
    [
        ("open window not yet applied", NOW - DAY, NOW + DAY, False, False, True),
        ("open-ended window not yet applied", NOW - DAY, None, False, False, True),
        ("open window already applied", NOW - DAY, NOW + DAY, True, False, False),
        ("closed window still applied", NOW - 2 * DAY, NOW - DAY, True, False, True),
        ("ended open-start window still applied", None, NOW - DAY, True, False, True),
        ("closed window not applied", NOW - 2 * DAY, NOW - DAY, False, False, False),
        ("future window not applied", NOW + DAY, None, False, False, False),
        ("open window with buyer conditions", NOW - DAY, NOW + DAY, False, True, False),
        ("future window still applied", NOW + DAY, None, True, False, True),
        (
            "applied row that gained buyer conditions",
            NOW - DAY,
            None,
            True,
            True,
            True,
        ),
        ("row without a window", None, None, False, False, False),
    ],
)
def test_find_window_price_rows_to_toggle(
    _case,
    valid_from,
    valid_to,
    is_applied,
    conditioned,
    expected,
    variant,
    customer_type,
):
    # given
    listing = variant.channel_listings.get()
    row = _create_row(
        listing,
        valid_from=valid_from,
        valid_to=valid_to,
        is_applied=is_applied,
        customer_type=customer_type if conditioned else None,
    )

    # when
    row_ids = find_window_price_rows_to_toggle(NOW, limit=10)

    # then
    assert row_ids == ([row.pk] if expected else [])


def test_find_window_price_rows_to_toggle_treats_a_value_condition_as_a_buyer_condition(
    variant, loyalty_customer_attribute
):
    # given
    listing = variant.channel_listings.get()
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )
    _create_row(listing, valid_from=NOW - DAY, valid_to=NOW + DAY, value=gold_value)

    # when
    row_ids = find_window_price_rows_to_toggle(NOW, limit=10)

    # then
    assert row_ids == []


def test_find_window_price_rows_to_toggle_returns_the_lowest_ids_up_to_the_limit(
    variant,
):
    # given
    listing = variant.channel_listings.get()
    rows = [
        _create_row(listing, valid_from=NOW - DAY, valid_to=NOW + DAY) for _ in range(3)
    ]

    # when
    row_ids = find_window_price_rows_to_toggle(NOW, limit=2)

    # then
    assert row_ids == [rows[0].pk, rows[1].pk]


def test_sync_window_price_rows_applies_and_withdraws_rows_and_marks_the_product_dirty(
    variant,
    product,
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    assert product_listing.discounted_price_dirty is False
    row_to_apply = _create_row(listing, valid_from=NOW - DAY, valid_to=NOW + DAY)
    row_to_withdraw = _create_row(
        listing, valid_from=NOW - 2 * DAY, valid_to=NOW - DAY, is_applied=True
    )
    untouched_row = _create_row(listing, valid_from=NOW + DAY, valid_to=None)

    # when
    sync_window_price_rows([row_to_apply.pk, row_to_withdraw.pk], NOW)

    # then
    row_to_apply.refresh_from_db(fields=["is_applied"])
    row_to_withdraw.refresh_from_db(fields=["is_applied"])
    untouched_row.refresh_from_db(fields=["is_applied"])
    assert row_to_apply.is_applied is True
    assert row_to_withdraw.is_applied is False
    assert untouched_row.is_applied is False
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_sync_window_price_rows_keeps_the_flags_when_the_product_is_already_dirty(
    variant, product
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    product_listing.discounted_price_dirty = True
    product_listing.save(update_fields=["discounted_price_dirty"])
    row_to_apply = _create_row(listing, valid_from=NOW - DAY, valid_to=NOW + DAY)
    row_to_withdraw = _create_row(
        listing, valid_from=NOW - 2 * DAY, valid_to=NOW - DAY, is_applied=True
    )

    # when
    sync_window_price_rows([row_to_apply.pk, row_to_withdraw.pk], NOW)

    # then
    row_to_apply.refresh_from_db(fields=["is_applied"])
    row_to_withdraw.refresh_from_db(fields=["is_applied"])
    assert row_to_apply.is_applied is False
    assert row_to_withdraw.is_applied is True
    assert find_window_price_rows_to_toggle(NOW, limit=10) == [
        row_to_apply.pk,
        row_to_withdraw.pk,
    ]


def test_sync_window_price_rows_flips_the_flag_once_the_product_is_clean_again(
    variant, product
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    product_listing.discounted_price_dirty = True
    product_listing.save(update_fields=["discounted_price_dirty"])
    row = _create_row(listing, valid_from=NOW - DAY, valid_to=NOW + DAY)
    sync_window_price_rows([row.pk], NOW)
    ProductChannelListing.objects.filter(pk=product_listing.pk).update(
        discounted_price_dirty=False
    )

    # when
    sync_window_price_rows([row.pk], NOW)

    # then
    row.refresh_from_db(fields=["is_applied"])
    assert row.is_applied is True
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_sync_window_price_rows_marks_the_product_dirty_when_no_flag_changes(
    variant, product
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    row = _create_row(
        listing, valid_from=NOW - DAY, valid_to=NOW + DAY, is_applied=True
    )

    # when
    sync_window_price_rows([row.pk], NOW)

    # then
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_sync_window_price_rows_withdraws_a_row_with_buyer_conditions(
    variant, customer_type
):
    # given
    listing = variant.channel_listings.get()
    row = _create_row(
        listing,
        valid_from=NOW - DAY,
        valid_to=NOW + DAY,
        is_applied=True,
        customer_type=customer_type,
    )

    # when
    sync_window_price_rows([row.pk], NOW)

    # then
    row.refresh_from_db(fields=["is_applied"])
    assert row.is_applied is False


def test_sync_window_price_rows_locks_the_rows_before_writing_them(variant):
    # given
    listing = variant.channel_listings.get()
    row = _create_row(listing, valid_from=NOW - DAY, valid_to=NOW + DAY)

    # when
    with CaptureQueriesContext(connection) as context:
        sync_window_price_rows([row.pk], NOW)

    # then
    row_queries = [
        query["sql"]
        for query in context.captured_queries
        if '"product_variantchannellistingprice"' in query["sql"]
        and ("FOR UPDATE" in query["sql"] or query["sql"].startswith("UPDATE"))
    ]
    assert len(row_queries) == 2
    lock_query, update_query = row_queries
    assert "FOR UPDATE" in lock_query
    assert "ORDER BY" in lock_query
    assert update_query.startswith("UPDATE")


def test_sync_window_price_rows_without_ids_runs_no_query():
    # when
    with CaptureQueriesContext(connection) as context:
        sync_window_price_rows([], NOW)

    # then
    assert context.captured_queries == []


def test_mark_products_dirty_for_listings_marks_only_the_listed_channels(
    product, channel_USD, channel_PLN
):
    # given
    variant = product.variants.first()
    usd_listing = variant.channel_listings.get(channel=channel_USD)
    ProductChannelListing.objects.create(
        product=product, channel=channel_PLN, is_published=True
    )

    # when
    marked_listing_ids = mark_products_dirty_for_listings([usd_listing.pk])

    # then
    assert marked_listing_ids == {usd_listing.pk}
    usd_product_listing = product.channel_listings.get(channel=channel_USD)
    pln_product_listing = product.channel_listings.get(channel=channel_PLN)
    assert usd_product_listing.discounted_price_dirty is True
    assert pln_product_listing.discounted_price_dirty is False


def test_mark_products_dirty_for_listings_skips_products_that_are_already_dirty(
    product, channel_USD
):
    # given
    listing = product.variants.first().channel_listings.get(channel=channel_USD)
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        discounted_price_dirty=True
    )

    # when
    marked_listing_ids = mark_products_dirty_for_listings([listing.pk])

    # then
    assert marked_listing_ids == set()
