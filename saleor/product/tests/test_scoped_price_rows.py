import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from ...attribute import AttributeInputType, AttributeType
from ...attribute.models import Attribute, AttributeValue
from ..error_codes import VariantChannelListingPriceErrorCode
from ..models import (
    VariantChannelListingPrice,
    VariantChannelListingPriceAttributeValue,
    VariantChannelListingPriceCustomerType,
)
from ..utils.scoped_price_rows import (
    ScopedPriceRowChanges,
    ScopedPriceRowData,
    count_scoped_price_rows_by_attribute_id,
    count_scoped_price_rows_by_attribute_value_id,
    count_scoped_price_rows_for_attribute_values,
    count_scoped_price_rows_for_customer_type,
    create_scoped_price_row,
    delete_scoped_price_row,
    get_ineligible_attribute_value_ids,
    update_scoped_price_row,
    validate_scoped_price_row_data,
)

NOW = datetime.datetime(2026, 10, 5, 12, tzinfo=datetime.UTC)
DAY = datetime.timedelta(days=1)
PRICE = Decimal("7.50")


def _data(
    *,
    price_amount=PRICE,
    customer_type_ids=(),
    attribute_value_ids=(),
    valid_from=None,
    valid_to=None,
):
    return ScopedPriceRowData(
        price_amount=price_amount,
        customer_type_ids=frozenset(customer_type_ids),
        attribute_value_ids=frozenset(attribute_value_ids),
        valid_from=valid_from,
        valid_to=valid_to,
    )


def _gold_value(loyalty_customer_attribute):
    return AttributeValue.objects.get(attribute=loyalty_customer_attribute, slug="gold")


@pytest.mark.parametrize(
    ("_case", "data_kwargs"),
    [
        ("customer_type_only", {"customer_type_ids": [1]}),
        ("attribute_value_only", {"attribute_value_ids": [1]}),
        ("window_start_only", {"valid_from": NOW}),
        ("window_end_only", {"valid_to": NOW}),
        ("ordered_window", {"valid_from": NOW, "valid_to": NOW + DAY}),
    ],
)
def test_validate_accepts_a_row_with_a_condition(_case, data_kwargs):
    validate_scoped_price_row_data(_data(**data_kwargs))


def test_validate_rejects_a_row_without_conditions():
    # when
    with pytest.raises(ValidationError) as exc_info:
        validate_scoped_price_row_data(_data())

    # then
    assert exc_info.value.code == VariantChannelListingPriceErrorCode.REQUIRED.value


@pytest.mark.parametrize(
    ("_case", "valid_from", "valid_to"),
    [
        ("empty_window", NOW, NOW),
        ("inverted_window", NOW + DAY, NOW),
    ],
)
def test_validate_rejects_a_window_that_does_not_end_after_it_starts(
    _case, valid_from, valid_to
):
    # when
    with pytest.raises(ValidationError) as exc_info:
        validate_scoped_price_row_data(_data(valid_from=valid_from, valid_to=valid_to))

    # then
    [error] = exc_info.value.error_dict["valid_to"]
    assert error.code == VariantChannelListingPriceErrorCode.INVALID.value


def test_get_ineligible_attribute_value_ids_keeps_choice_customer_values(
    loyalty_customer_attribute,
):
    # given
    assert loyalty_customer_attribute.input_type == AttributeInputType.DROPDOWN
    gold_value = _gold_value(loyalty_customer_attribute)

    # when
    ineligible_ids = get_ineligible_attribute_value_ids([gold_value.pk])

    # then
    assert ineligible_ids == set()


def test_get_ineligible_attribute_value_ids_rejects_product_and_text_values(
    color_attribute, description_customer_attribute, loyalty_customer_attribute
):
    # given
    assert color_attribute.type == AttributeType.PRODUCT_TYPE
    assert description_customer_attribute.input_type == AttributeInputType.PLAIN_TEXT
    color_value = color_attribute.values.first()
    text_value = AttributeValue.objects.create(
        attribute=description_customer_attribute, name="Note", slug="note"
    )
    gold_value = _gold_value(loyalty_customer_attribute)

    # when
    ineligible_ids = get_ineligible_attribute_value_ids(
        [color_value.pk, text_value.pk, gold_value.pk]
    )

    # then
    assert ineligible_ids == {color_value.pk, text_value.pk}


def test_create_stores_the_conditions(
    variant, customer_type, loyalty_customer_attribute
):
    # given
    listing = variant.channel_listings.get()
    gold_value = _gold_value(loyalty_customer_attribute)
    data = _data(
        customer_type_ids=[customer_type.pk],
        attribute_value_ids=[gold_value.pk],
        valid_from=NOW,
    )

    # when
    row = create_scoped_price_row(listing, data, NOW)

    # then
    row = VariantChannelListingPrice.objects.get(pk=row.pk)
    assert row.variant_channel_listing_id == listing.pk
    assert row.currency == listing.currency
    assert row.price_amount == PRICE
    assert row.valid_from == NOW
    assert row.valid_to is None
    assert list(row.customer_types.values_list("pk", flat=True)) == [customer_type.pk]
    assert list(row.attribute_values.values_list("pk", flat=True)) == [gold_value.pk]
    assert row.is_applied is False


def test_create_applies_an_open_window_row_and_marks_the_product_dirty(
    variant, product
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    assert product_listing.discounted_price_dirty is False

    # when
    row = create_scoped_price_row(
        listing, _data(valid_from=NOW - DAY, valid_to=NOW + DAY), NOW
    )

    # then
    row.refresh_from_db(fields=["is_applied"])
    assert row.is_applied is True
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_create_rejects_the_row_above_the_listing_cap(variant):
    # given
    listing = variant.channel_listings.get()
    create_scoped_price_row(listing, _data(valid_from=NOW), NOW)

    # when
    with (
        patch(
            "saleor.product.utils.scoped_price_rows.MAX_SCOPED_PRICES_PER_LISTING", 1
        ),
        pytest.raises(ValidationError) as exc_info,
    ):
        create_scoped_price_row(listing, _data(valid_from=NOW), NOW)

    # then
    [error] = exc_info.value.error_dict["variant_channel_listing"]
    assert error.code == VariantChannelListingPriceErrorCode.LIMIT_EXCEEDED.value
    assert listing.prices.count() == 1


def test_create_locks_the_product_channel_listing_before_writing(variant):
    # given
    listing = variant.channel_listings.get()
    create_scoped_price_row(listing, _data(valid_from=NOW), NOW)

    # when
    with CaptureQueriesContext(connection) as ctx:
        create_scoped_price_row(listing, _data(valid_from=NOW), NOW)

    # then
    lock_and_insert_queries = [
        query["sql"]
        for query in ctx.captured_queries
        if (
            "FOR UPDATE" in query["sql"]
            and "product_productchannellisting" in query["sql"]
        )
        or (
            query["sql"].startswith("INSERT")
            and "product_variantchannellistingprice" in query["sql"]
        )
    ]
    # the cap lock, the insert, then the lock the dirty mark takes
    assert len(lock_and_insert_queries) == 3
    assert "FOR UPDATE" in lock_and_insert_queries[0]
    assert "ORDER BY" in lock_and_insert_queries[0]
    assert lock_and_insert_queries[1].startswith("INSERT")
    assert "FOR UPDATE" in lock_and_insert_queries[2]


def test_update_replaces_the_conditions_as_sets(
    variant, customer_type, default_customer_type, loyalty_customer_attribute
):
    # given
    listing = variant.channel_listings.get()
    gold_value = _gold_value(loyalty_customer_attribute)
    silver_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="silver"
    )
    row = create_scoped_price_row(
        listing,
        _data(
            customer_type_ids=[customer_type.pk], attribute_value_ids=[gold_value.pk]
        ),
        NOW,
    )
    new_price = Decimal("6.25")

    # when
    update_scoped_price_row(
        row,
        ScopedPriceRowChanges(
            price_amount=new_price,
            customer_type_ids=frozenset([default_customer_type.pk]),
            attribute_value_ids=frozenset([gold_value.pk, silver_value.pk]),
        ),
        NOW,
    )

    # then
    row.refresh_from_db()
    assert row.price_amount == new_price
    assert list(row.customer_types.values_list("pk", flat=True)) == [
        default_customer_type.pk
    ]
    assert sorted(row.attribute_values.values_list("pk", flat=True)) == sorted(
        [gold_value.pk, silver_value.pk]
    )


def test_update_withdraws_an_applied_row_that_gains_a_buyer_condition(
    variant, product, customer_type
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    row = create_scoped_price_row(
        listing, _data(valid_from=NOW - DAY, valid_to=NOW + DAY), NOW
    )
    row.refresh_from_db(fields=["is_applied"])
    assert row.is_applied is True
    product_listing.discounted_price_dirty = False
    product_listing.save(update_fields=["discounted_price_dirty"])

    # when
    update_scoped_price_row(
        row, ScopedPriceRowChanges(customer_type_ids=frozenset([customer_type.pk])), NOW
    )

    # then
    row.refresh_from_db(fields=["is_applied"])
    assert row.is_applied is False
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_update_withdraws_an_applied_row_whose_window_moved_to_the_future(
    variant, product
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    row = create_scoped_price_row(listing, _data(valid_from=NOW - DAY), NOW)
    row.refresh_from_db(fields=["is_applied"])
    assert row.is_applied is True
    product_listing.discounted_price_dirty = False
    product_listing.save(update_fields=["discounted_price_dirty"])

    # when
    update_scoped_price_row(row, ScopedPriceRowChanges(valid_from=NOW + DAY), NOW)

    # then
    row.refresh_from_db(fields=["is_applied", "valid_from"])
    assert row.is_applied is False
    assert row.valid_from == NOW + DAY
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_update_of_the_price_marks_the_product_dirty_and_keeps_the_flag(
    variant, product
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    row = create_scoped_price_row(listing, _data(valid_from=NOW - DAY), NOW)
    product_listing.discounted_price_dirty = False
    product_listing.save(update_fields=["discounted_price_dirty"])
    new_price = Decimal(3)

    # when
    update_scoped_price_row(row, ScopedPriceRowChanges(price_amount=new_price), NOW)

    # then
    row.refresh_from_db(fields=["is_applied", "price_amount"])
    assert row.is_applied is True
    assert row.price_amount == new_price
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_delete_removes_the_row_and_marks_the_product_dirty(
    variant, product, customer_type, loyalty_customer_attribute
):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    gold_value = _gold_value(loyalty_customer_attribute)
    row = create_scoped_price_row(
        listing,
        _data(
            customer_type_ids=[customer_type.pk], attribute_value_ids=[gold_value.pk]
        ),
        NOW,
    )
    assert product_listing.discounted_price_dirty is False

    # when
    delete_scoped_price_row(row)

    # then
    assert VariantChannelListingPrice.objects.filter(pk=row.pk).exists() is False
    assert (
        VariantChannelListingPriceCustomerType.objects.filter(
            listing_price_id=row.pk
        ).exists()
        is False
    )
    assert (
        VariantChannelListingPriceAttributeValue.objects.filter(
            listing_price_id=row.pk
        ).exists()
        is False
    )
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_delete_of_a_missing_row_is_a_no_op(variant, product):
    # given
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    row = create_scoped_price_row(listing, _data(valid_from=NOW + DAY), NOW)
    product_listing.discounted_price_dirty = False
    product_listing.save(update_fields=["discounted_price_dirty"])
    VariantChannelListingPrice.objects.filter(pk=row.pk).delete()

    # when
    delete_scoped_price_row(row)

    # then
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is False


def test_create_defaults_now_to_the_current_time(variant):
    # given
    listing = variant.channel_listings.get()
    valid_from = timezone.now() - DAY

    # when
    row = create_scoped_price_row(listing, _data(valid_from=valid_from))

    # then
    row.refresh_from_db(fields=["is_applied"])
    assert row.is_applied is True


def test_count_rows_for_customer_type(
    variant_channel_listing_price_for_customer_type, customer_type
):
    # when
    row_count = count_scoped_price_rows_for_customer_type(customer_type.pk)

    # then
    assert row_count == 1


def test_count_rows_by_attribute_value_id(
    variant_channel_listing_price_for_attribute_value, loyalty_customer_attribute
):
    # given
    gold_value = _gold_value(loyalty_customer_attribute)
    silver_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="silver"
    )

    # when
    row_counts = count_scoped_price_rows_by_attribute_value_id(
        [gold_value.pk, silver_value.pk]
    )

    # then
    assert row_counts == {gold_value.pk: 1}


def test_count_rows_by_attribute_id_counts_a_row_once_per_attribute(
    variant, loyalty_customer_attribute
):
    # given
    listing = variant.channel_listings.get()
    value_ids = list(loyalty_customer_attribute.values.values_list("pk", flat=True))
    assert len(value_ids) == 2
    create_scoped_price_row(listing, _data(attribute_value_ids=value_ids), NOW)
    other_attribute = Attribute.objects.create(
        slug="other", name="Other", type=AttributeType.CUSTOMER_TYPE
    )

    # when
    row_counts = count_scoped_price_rows_by_attribute_id(
        [loyalty_customer_attribute.pk, other_attribute.pk]
    )

    # then
    assert row_counts == {loyalty_customer_attribute.pk: 1}


def test_update_validates_the_merged_state(
    variant, variant_channel_listing_price_for_customer_type
):
    # given
    row = variant_channel_listing_price_for_customer_type

    # when
    with pytest.raises(ValidationError) as exc_info:
        update_scoped_price_row(
            row, ScopedPriceRowChanges(customer_type_ids=frozenset()), NOW
        )

    # then
    assert exc_info.value.code == VariantChannelListingPriceErrorCode.REQUIRED.value
    assert row.customer_types.exists() is True


def test_update_merges_the_changes_with_the_locked_row(
    variant, variant_channel_listing_price_for_customer_type, customer_type
):
    # given
    row = variant_channel_listing_price_for_customer_type
    # a concurrent writer changed the price after the mutation read the row
    concurrent_price = Decimal(4)
    VariantChannelListingPrice.objects.filter(pk=row.pk).update(
        price_amount=concurrent_price
    )
    assert row.price_amount != concurrent_price

    # when
    update_scoped_price_row(row, ScopedPriceRowChanges(valid_from=NOW), NOW)

    # then
    row.refresh_from_db(fields=["price_amount", "valid_from"])
    assert row.price_amount == concurrent_price
    assert row.valid_from == NOW
    assert list(row.customer_types.values_list("pk", flat=True)) == [customer_type.pk]


def test_create_validates_the_data():
    # when
    with pytest.raises(ValidationError) as exc_info:
        create_scoped_price_row(None, _data(), NOW)

    # then
    assert exc_info.value.code == VariantChannelListingPriceErrorCode.REQUIRED.value


def test_count_rows_for_attribute_values_counts_a_row_once(
    variant, loyalty_customer_attribute
):
    # given
    listing = variant.channel_listings.get()
    value_ids = list(loyalty_customer_attribute.values.values_list("pk", flat=True))
    create_scoped_price_row(listing, _data(attribute_value_ids=value_ids), NOW)

    # when
    row_count = count_scoped_price_rows_for_attribute_values(value_ids)

    # then
    assert row_count == 1
