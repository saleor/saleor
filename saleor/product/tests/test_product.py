import os
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
import pytz
from freezegun import freeze_time
from prices import Money

from ...account import events as account_events
from ...attribute.utils import associate_attribute_values_to_instance
from ...discount import RewardValueType
from ...discount.models import PromotionRule
from ...graphql.product.filters import (
    _clean_product_attributes_boolean_filter_input,
    _clean_product_attributes_date_time_range_filter_input,
    filter_products_by_attributes_values,
)
from .. import ProductTypeKind, models
from ..tasks import update_variants_names
from ..utils.costs import get_margin_for_variant_channel_listing
from ..utils.digital_products import increment_download_count


def test_filtering_by_attribute(
    db,
    color_attribute,
    size_attribute,
    category,
    channel_USD,
    settings,
    date_attribute,
    date_time_attribute,
    boolean_attribute,
):
    product_type_a = models.ProductType.objects.create(
        name="New class",
        slug="new-class1",
        has_variants=True,
        kind=ProductTypeKind.NORMAL,
    )
    product_type_a.product_attributes.add(color_attribute)
    product_type_b = models.ProductType.objects.create(
        name="New class",
        slug="new-class2",
        has_variants=True,
        kind=ProductTypeKind.NORMAL,
    )
    product_type_b.variant_attributes.add(color_attribute)
    product_a = models.Product.objects.create(
        name="Test product a",
        slug="test-product-a",
        product_type=product_type_a,
        category=category,
    )
    variant_a = models.ProductVariant.objects.create(product=product_a, sku="1234")
    models.ProductVariantChannelListing.objects.create(
        variant=variant_a,
        channel=channel_USD,
        cost_price_amount=Decimal(1),
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    product_b = models.Product.objects.create(
        name="Test product b",
        slug="test-product-b",
        product_type=product_type_b,
        category=category,
    )
    variant_b = models.ProductVariant.objects.create(product=product_b, sku="12345")
    models.ProductVariantChannelListing.objects.create(
        variant=variant_b,
        channel=channel_USD,
        cost_price_amount=Decimal(1),
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    color = color_attribute.values.first()
    color_2 = color_attribute.values.last()

    # Associate color to a product and a variant
    associate_attribute_values_to_instance(
        product_a,
        {color_attribute.pk: [color]},
    )
    associate_attribute_values_to_instance(
        variant_b,
        {color_attribute.pk: [color]},
    )

    product_qs = models.Product.objects.all().values_list("pk", flat=True)

    filters = {color_attribute.pk: [color.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)
    assert product_b.pk in list(filtered)

    associate_attribute_values_to_instance(
        product_a,
        {color_attribute.pk: [color_2]},
    )

    filters = {color_attribute.pk: [color.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)

    assert product_a.pk not in list(filtered)
    assert product_b.pk in list(filtered)

    filters = {color_attribute.pk: [color_2.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)
    assert product_b.pk not in list(filtered)

    # Filter by multiple values, should trigger a OR condition
    filters = {color_attribute.pk: [color.pk, color_2.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)
    assert product_b.pk in list(filtered)

    # Associate additional attribute to a product
    size = size_attribute.values.first()
    product_type_a.product_attributes.add(size_attribute)
    associate_attribute_values_to_instance(
        product_a,
        {size_attribute.pk: [size]},
    )

    # Filter by multiple attributes
    filters = {color_attribute.pk: [color_2.pk], size_attribute.pk: [size.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)

    # Filter by date attributes
    product_type_a.product_attributes.add(date_attribute)
    product_type_b.product_attributes.add(date_attribute)

    date = date_attribute.values.first()
    associate_attribute_values_to_instance(
        product_a,
        {date_attribute.pk: [date]},
    )

    date_2 = date_attribute.values.last()
    associate_attribute_values_to_instance(
        product_b,
        {date_attribute.pk: [date_2]},
    )

    filters = {date_attribute.pk: [date.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)

    filters = {date_attribute.pk: [date.pk, date_2.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)
    assert product_b.pk in list(filtered)


def test_clean_product_attributes_date_time_range_filter_input(
    date_attribute, date_time_attribute, settings
):
    # filter date attribute
    filter_value = [
        (
            date_attribute.slug,
            {"gte": datetime(2020, 10, 5, tzinfo=pytz.utc)},
        )
    ]
    values_qs = _clean_product_attributes_date_time_range_filter_input(
        filter_value, settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    assert set(date_attribute.values.all()) == set(values_qs.all())

    filter_value = [
        (
            date_attribute.slug,
            {"gte": datetime(2020, 10, 5).date(), "lte": datetime(2020, 11, 4).date()},
        )
    ]
    values_qs = _clean_product_attributes_date_time_range_filter_input(
        filter_value, settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    assert {date_attribute.values.first().pk} == set(
        values_qs.values_list("pk", flat=True)
    )

    # filter date time attribute
    filter_value = [
        (
            date_attribute.slug,
            {"lte": datetime(2020, 11, 4, tzinfo=timezone.utc)},
        )
    ]
    values_qs = _clean_product_attributes_date_time_range_filter_input(
        filter_value, settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    assert {date_attribute.values.first().pk} == set(
        values_qs.values_list("pk", flat=True)
    )

    filter_value = [
        (
            date_attribute.slug,
            {"lte": datetime(2020, 10, 4, tzinfo=timezone.utc)},
        )
    ]
    values_qs = _clean_product_attributes_date_time_range_filter_input(
        filter_value, settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    assert values_qs.exists() is False


def test_clean_product_attributes_boolean_filter_input(boolean_attribute, settings):
    filter_value = [(boolean_attribute.slug, True)]
    queries = defaultdict(list)
    _clean_product_attributes_boolean_filter_input(
        filter_value, queries, settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    assert dict(queries) == {
        boolean_attribute.pk: [boolean_attribute.values.first().pk]
    }

    filter_value = [(boolean_attribute.slug, False)]
    queries = defaultdict(list)
    _clean_product_attributes_boolean_filter_input(
        filter_value, queries, settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    assert dict(queries) == {boolean_attribute.pk: [boolean_attribute.values.last().pk]}

    filter_value = [(boolean_attribute.slug, True), (boolean_attribute.slug, False)]
    queries = defaultdict(list)
    _clean_product_attributes_boolean_filter_input(
        filter_value, queries, settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    assert dict(queries) == {
        boolean_attribute.pk: list(
            boolean_attribute.values.all().values_list("pk", flat=True)
        )
    }


@pytest.mark.parametrize(
    ("price", "discounted_price"),
    [
        (Decimal("10.00"), Decimal("8.00")),
        (Decimal("10.00"), None),
        (Decimal("10.00"), Decimal("10.00")),
    ],
)
def test_get_price(
    price,
    discounted_price,
    product_type,
    category,
    channel_USD,
):
    # given
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
    )
    variant = product.variants.create()
    channel_listing = models.ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=price,
        discounted_price_amount=discounted_price,
        currency=channel_USD.currency_code,
    )

    # when
    price = variant.get_price(channel_listing)

    # then
    assert price.amount == discounted_price or price


def test_get_price_overridden_price_no_discount(
    product_type,
    category,
    channel_USD,
):
    # given
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
    )
    variant = product.variants.create()
    price_amount = Decimal(15)
    channel_listing = models.ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=price_amount,
        currency=channel_USD.currency_code,
    )
    price_override = Decimal(10)

    # when
    price = variant.get_price(channel_listing, price_override=price_override)

    # then
    assert price.amount == price_override


def test_get_price_overridden_price_with_discount(
    product_type,
    category,
    channel_USD,
    catalogue_promotion_without_rules,
):
    # given
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
    )
    variant = product.variants.create()
    price_amount = Decimal(15)
    channel_listing = models.ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=price_amount,
        currency=channel_USD.currency_code,
    )
    price_override = Decimal("20")

    reward_value_1 = Decimal("10")
    reward_value_2 = Decimal("5")
    rule_1, rule_2 = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                promotion=catalogue_promotion_without_rules,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [
                            graphene.Node.to_global_id("Product", variant.product.id)
                        ]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=reward_value_1,
            ),
            PromotionRule(
                promotion=catalogue_promotion_without_rules,
                catalogue_predicate={
                    "variantPredicate": {
                        "ids": [
                            graphene.Node.to_global_id(
                                "ProductVariant", variant.product.id
                            )
                        ]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value_2,
            ),
        ]
    )

    models.VariantChannelListingPromotionRule.objects.bulk_create(
        [
            models.VariantChannelListingPromotionRule(
                variant_channel_listing=channel_listing,
                promotion_rule=rule_1,
                discount_amount=reward_value_1,
                currency=channel_USD.currency_code,
            ),
            models.VariantChannelListingPromotionRule(
                variant_channel_listing=channel_listing,
                promotion_rule=rule_2,
                discount_amount=reward_value_2,
                currency=channel_USD.currency_code,
            ),
        ]
    )

    # when
    price = variant.get_price(
        channel_listing, price_override=price_override, promotion_rules=[rule_1, rule_2]
    )

    # then
    assert price.amount == price_override - reward_value_2 - (
        reward_value_1 / 100 * price_override
    )


def test_digital_product_view(client, digital_content_url):
    """Ensure a non-expired digital good can be downloaded and results in an event."""

    url = digital_content_url.get_absolute_url()
    response = client.get(url)
    filename = os.path.basename(digital_content_url.content.content_file.name)

    assert response.status_code == 200
    assert response["content-type"] == "image/jpeg"
    assert response["content-disposition"] == f'attachment; filename="{filename}"'

    # Ensure an event was generated from downloading a digital good.
    # The validity of this event is checked in test_digital_product_increment_download
    assert account_events.CustomerEvent.objects.exists()


@pytest.mark.parametrize(
    ("is_user_null", "is_line_null"), [(False, False), (False, True), (True, True)]
)
def test_digital_product_increment_download(
    client,
    customer_user,
    digital_content_url: models.DigitalContentUrl,
    is_user_null,
    is_line_null,
):
    """Ensure a digital good can be downloaded without it belonging to an order or user."""

    expected_user = customer_user

    if is_line_null:
        expected_user = None
        digital_content_url.line = None
        digital_content_url.save(update_fields=["line"])
    elif is_user_null:
        expected_user = None
        digital_content_url.line.user = None
        digital_content_url.line.save(update_fields=["user"])

    expected_new_download_count = digital_content_url.download_num + 1
    increment_download_count(digital_content_url)
    assert digital_content_url.download_num == expected_new_download_count

    if expected_user is None:
        # Ensure an event was not generated from downloading a digital good
        # as no user could be found
        assert not account_events.CustomerEvent.objects.exists()
        return

    download_event = account_events.CustomerEvent.objects.get()
    assert download_event.type == account_events.CustomerEvents.DIGITAL_LINK_DOWNLOADED
    assert download_event.user == expected_user
    assert download_event.order == digital_content_url.line.order
    assert download_event.parameters == {
        "order_line_pk": str(digital_content_url.line.pk)
    }


def test_digital_product_view_url_downloaded_max_times(client, digital_content):
    digital_content.use_default_settings = False
    digital_content.max_downloads = 1
    digital_content.save()
    digital_content_url = models.DigitalContentUrl.objects.create(
        content=digital_content
    )

    url = digital_content_url.get_absolute_url()
    response = client.get(url)

    # first download
    assert response.status_code == 200

    # second download
    response = client.get(url)
    assert response.status_code == 404


def test_digital_product_view_url_expired(client, digital_content):
    digital_content.use_default_settings = False
    digital_content.url_valid_days = 10
    digital_content.save()

    with freeze_time("2018-05-31 12:00:01"):
        digital_content_url = models.DigitalContentUrl.objects.create(
            content=digital_content
        )

    url = digital_content_url.get_absolute_url()
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("price", "cost"),
    [(Money("0", "USD"), Money("1", "USD")), (Money("2", "USD"), None)],
)
def test_costs_get_margin_for_variant_channel_listing(
    variant, price, cost, channel_USD
):
    variant_channel_listing = variant.channel_listings.filter(
        channel_id=channel_USD.id
    ).first()
    variant_channel_listing.cost_price = cost
    variant_channel_listing.price = price
    assert not get_margin_for_variant_channel_listing(variant_channel_listing)


@patch("saleor.product.signals.delete_from_storage_task.delay")
def test_product_media_delete(delete_from_storage_task_mock, product_with_image):
    # given
    media = product_with_image.media.first()

    # when
    media.delete()

    # then
    delete_from_storage_task_mock.assert_called_once_with(media.image.name)


@patch("saleor.product.tasks._update_variants_names")
def test_product_update_variants_names(mock__update_variants_names, product_type):
    variant_attributes = [product_type.variant_attributes.first()]
    variant_attr_ids = [attr.pk for attr in variant_attributes]
    update_variants_names(product_type.pk, variant_attr_ids)
    assert mock__update_variants_names.call_count == 1
