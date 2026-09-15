import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from ....attribute.models import AttributeValue
from ...models import (
    VariantChannelListingPrice,
    VariantChannelListingPriceAttributeValue,
    VariantChannelListingPriceCustomerType,
)

__all__ = [
    "variant_channel_listing_price",
    "variant_channel_listing_price_for_customer_type",
    "variant_channel_listing_price_for_attribute_value",
]


@pytest.fixture
def variant_channel_listing_price(variant):
    """Create a validity-window row on the variant's listing with no buyer conditions."""
    listing = variant.channel_listings.get()
    now = timezone.now()
    return VariantChannelListingPrice.objects.create(
        variant_channel_listing=listing,
        currency=listing.currency,
        price_amount=Decimal(9),
        valid_from=now,
        valid_to=now + datetime.timedelta(days=30),
    )


@pytest.fixture
def variant_channel_listing_price_for_customer_type(variant, customer_type):
    """Create a row that applies to customers of the given type only."""
    listing = variant.channel_listings.get()
    listing_price = VariantChannelListingPrice.objects.create(
        variant_channel_listing=listing,
        currency=listing.currency,
        price_amount=Decimal(8),
    )
    VariantChannelListingPriceCustomerType.objects.create(
        listing_price=listing_price, customer_type=customer_type
    )
    return listing_price


@pytest.fixture
def variant_channel_listing_price_for_attribute_value(
    variant, loyalty_customer_attribute
):
    """Create a row that applies to customers with the gold loyalty level only."""
    listing = variant.channel_listings.get()
    listing_price = VariantChannelListingPrice.objects.create(
        variant_channel_listing=listing,
        currency=listing.currency,
        price_amount=Decimal(7),
    )
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )
    VariantChannelListingPriceAttributeValue.objects.create(
        listing_price=listing_price, value=gold_value
    )
    return listing_price
