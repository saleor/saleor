import datetime
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from ...account.models import CustomerType
from ...attribute.models import Attribute, AttributeValue
from ..lock_objects import variant_channel_listing_price_qs_select_for_update
from ..models import (
    VariantChannelListingPrice,
    VariantChannelListingPriceAttributeValue,
    VariantChannelListingPriceCustomerType,
)


def test_negative_price_is_rejected(variant_channel_listing_price):
    # given
    variant_channel_listing_price.price_amount = Decimal(-1)

    # when / then
    with (
        pytest.raises(
            IntegrityError, match="variantchannellistingprice_price_non_negative"
        ),
    ):
        variant_channel_listing_price.save(update_fields=["price_amount"])


@pytest.mark.parametrize(
    ("_case", "valid_to_offset"),
    [
        ("valid_to_before_valid_from", datetime.timedelta(days=-1)),
        ("valid_to_equal_to_valid_from", datetime.timedelta(0)),
    ],
)
def test_inverted_validity_window_is_rejected(
    _case, valid_to_offset, variant_channel_listing_price
):
    # given
    valid_from = timezone.now()
    variant_channel_listing_price.valid_from = valid_from
    variant_channel_listing_price.valid_to = valid_from + valid_to_offset

    # when / then
    with (
        pytest.raises(IntegrityError, match="variantchannellistingprice_valid_window"),
    ):
        variant_channel_listing_price.save(update_fields=["valid_from", "valid_to"])


@pytest.mark.parametrize(
    ("_case", "valid_from", "valid_to"),
    [
        ("open_window", None, None),
        ("only_valid_from", timezone.now(), None),
        ("only_valid_to", None, timezone.now()),
    ],
)
def test_partial_validity_window_is_allowed(
    _case, valid_from, valid_to, variant_channel_listing_price
):
    # given
    variant_channel_listing_price.valid_from = valid_from
    variant_channel_listing_price.valid_to = valid_to

    # when / then: the window constraint only rejects an inverted window, so
    # saving with a missing bound must not raise.
    variant_channel_listing_price.save(update_fields=["valid_from", "valid_to"])


def test_duplicate_customer_type_condition_is_rejected(
    variant_channel_listing_price_for_customer_type, customer_type
):
    # when / then
    with (
        pytest.raises(
            IntegrityError, match="variantchannellistingprice_customer_type_unique"
        ),
    ):
        VariantChannelListingPriceCustomerType.objects.create(
            listing_price=variant_channel_listing_price_for_customer_type,
            customer_type=customer_type,
        )


def test_duplicate_attribute_value_condition_is_rejected(
    variant_channel_listing_price_for_attribute_value, loyalty_customer_attribute
):
    # given
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )

    # when / then
    with (
        pytest.raises(
            IntegrityError, match="variantchannellistingprice_attribute_value_unique"
        ),
    ):
        VariantChannelListingPriceAttributeValue.objects.create(
            listing_price=variant_channel_listing_price_for_attribute_value,
            value=gold_value,
        )


def test_deleting_referenced_customer_type_is_protected(
    variant_channel_listing_price_for_customer_type, customer_type
):
    # when / then
    with pytest.raises(
        ProtectedError, match="VariantChannelListingPriceCustomerType.customer_type"
    ):
        customer_type.delete()

    assert CustomerType.objects.get(pk=customer_type.pk) == customer_type
    condition = (
        variant_channel_listing_price_for_customer_type.customer_type_conditions.get()
    )
    assert condition.customer_type == customer_type


def test_deleting_referenced_attribute_value_is_protected(
    variant_channel_listing_price_for_attribute_value, loyalty_customer_attribute
):
    # given
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )

    # when / then
    with pytest.raises(
        ProtectedError, match="VariantChannelListingPriceAttributeValue.value"
    ):
        gold_value.delete()

    assert AttributeValue.objects.get(pk=gold_value.pk) == gold_value
    condition = variant_channel_listing_price_for_attribute_value.attribute_value_conditions.get()
    assert condition.value == gold_value


def test_deleting_attribute_of_referenced_value_is_protected(
    variant_channel_listing_price_for_attribute_value, loyalty_customer_attribute
):
    # given
    condition = variant_channel_listing_price_for_attribute_value.attribute_value_conditions.get()

    # when / then: the delete cascades to the values, whose condition row is
    # protected, so the whole attribute delete is refused.
    with pytest.raises(ProtectedError) as exc_info:
        loyalty_customer_attribute.delete()

    assert exc_info.value.protected_objects == {condition}
    assert (
        Attribute.objects.get(pk=loyalty_customer_attribute.pk)
        == loyalty_customer_attribute
    )
    assert AttributeValue.objects.get(pk=condition.value_id) == condition.value


def test_deleting_listing_cascades_prices_and_conditions(
    variant,
    variant_channel_listing_price,
    variant_channel_listing_price_for_customer_type,
    variant_channel_listing_price_for_attribute_value,
):
    # given
    listing = variant.channel_listings.get()
    assert listing.prices.count() == 3

    # when
    listing.delete()

    # then
    assert VariantChannelListingPrice.objects.exists() is False
    assert VariantChannelListingPriceCustomerType.objects.exists() is False
    assert VariantChannelListingPriceAttributeValue.objects.exists() is False


def test_select_for_update_locks_rows_before_write(
    variant_channel_listing_price, assert_locks_rows_before_write
):
    # given
    new_price_amount = Decimal(5)

    # when
    with assert_locks_rows_before_write(), transaction.atomic():
        locked_pks = list(
            variant_channel_listing_price_qs_select_for_update()
            .filter(pk=variant_channel_listing_price.pk)
            .values_list("pk", flat=True)
        )
        VariantChannelListingPrice.objects.filter(pk__in=locked_pks).update(
            price_amount=new_price_amount
        )

    # then
    variant_channel_listing_price.refresh_from_db(fields=("price_amount",))
    assert variant_channel_listing_price.price_amount == new_price_amount
