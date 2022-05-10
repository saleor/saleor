import os
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from prices import Money

from ...account import events as account_events
from ...attribute.utils import associate_attribute_values_to_instance
from ...graphql.product.filters import (
    _clean_product_attributes_boolean_filter_input,
    _clean_product_attributes_date_time_range_filter_input,
    filter_products_by_attributes_values,
)
from .. import ProductTypeKind, models
from ..models import DigitalContentUrl
from ..thumbnails import create_product_thumbnails
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
    associate_attribute_values_to_instance(product_a, color_attribute, color)
    associate_attribute_values_to_instance(variant_b, color_attribute, color)

    product_qs = models.Product.objects.all().values_list("pk", flat=True)

    filters = {color_attribute.pk: [color.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)
    assert product_b.pk in list(filtered)

    associate_attribute_values_to_instance(product_a, color_attribute, color_2)

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
    associate_attribute_values_to_instance(product_a, size_attribute, size)

    # Filter by multiple attributes
    filters = {color_attribute.pk: [color_2.pk], size_attribute.pk: [size.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)

    # Filter by date attributes
    product_type_a.product_attributes.add(date_attribute)
    product_type_b.product_attributes.add(date_attribute)

    date = date_attribute.values.first()
    associate_attribute_values_to_instance(product_a, date_attribute, date)

    date_2 = date_attribute.values.last()
    associate_attribute_values_to_instance(product_b, date_attribute, date_2)

    filters = {date_attribute.pk: [date.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)

    filters = {date_attribute.pk: [date.pk, date_2.pk]}
    filtered = filter_products_by_attributes_values(product_qs, filters)
    assert product_a.pk in list(filtered)
    assert product_b.pk in list(filtered)


def test_clean_product_attributes_date_time_range_filter_input(
    date_attribute, date_time_attribute
):
    # filter date attribute
    filter_value = [
        (
            date_attribute.slug,
            {"gte": datetime(2020, 10, 5).date()},
        )
    ]
    queries = defaultdict(list)
    _clean_product_attributes_date_time_range_filter_input(
        filter_value, queries, is_date=True
    )

    assert dict(queries) == {
        date_attribute.pk: list(
            date_attribute.values.all().values_list("pk", flat=True)
        )
    }

    filter_value = [
        (
            date_attribute.slug,
            {"gte": datetime(2020, 10, 5).date(), "lte": datetime(2020, 11, 4).date()},
        )
    ]
    queries = defaultdict(list)
    _clean_product_attributes_date_time_range_filter_input(
        filter_value, queries, is_date=True
    )

    assert dict(queries) == {date_attribute.pk: [date_attribute.values.first().pk]}

    # filter date time attribute
    filter_value = [
        (
            date_attribute.slug,
            {"lte": datetime(2020, 11, 4, tzinfo=timezone.utc)},
        )
    ]
    queries = defaultdict(list)
    _clean_product_attributes_date_time_range_filter_input(filter_value, queries)

    assert dict(queries) == {date_attribute.pk: [date_attribute.values.first().pk]}

    filter_value = [
        (
            date_attribute.slug,
            {"lte": datetime(2020, 10, 4, tzinfo=timezone.utc)},
        )
    ]
    queries = defaultdict(list)
    _clean_product_attributes_date_time_range_filter_input(filter_value, queries)

    assert dict(queries) == {date_attribute.pk: []}


def test_clean_product_attributes_boolean_filter_input(boolean_attribute):
    filter_value = [(boolean_attribute.slug, True)]
    queries = defaultdict(list)
    _clean_product_attributes_boolean_filter_input(filter_value, queries)

    assert dict(queries) == {
        boolean_attribute.pk: [boolean_attribute.values.first().pk]
    }

    filter_value = [(boolean_attribute.slug, False)]
    queries = defaultdict(list)
    _clean_product_attributes_boolean_filter_input(filter_value, queries)

    assert dict(queries) == {boolean_attribute.pk: [boolean_attribute.values.last().pk]}

    filter_value = [(boolean_attribute.slug, True), (boolean_attribute.slug, False)]
    queries = defaultdict(list)
    _clean_product_attributes_boolean_filter_input(filter_value, queries)

    assert dict(queries) == {
        boolean_attribute.pk: list(
            boolean_attribute.values.all().values_list("pk", flat=True)
        )
    }


@pytest.mark.parametrize(
    "expected_price, include_discounts",
    [(Decimal("10.00"), True), (Decimal("15.0"), False)],
)
def test_get_price(
    product_type,
    category,
    sale,
    expected_price,
    include_discounts,
    site_settings,
    discount_info,
    channel_USD,
):
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
    )
    variant = product.variants.create()
    channel_listing = models.ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(15),
        currency=channel_USD.currency_code,
    )
    discounts = [discount_info] if include_discounts else []
    price = variant.get_price(product, [], channel_USD, channel_listing, discounts)
    assert price.amount == expected_price


def test_product_get_price_do_not_charge_taxes(
    product_type, category, discount_info, channel_USD
):
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
        charge_taxes=False,
    )
    variant = product.variants.create()
    channel_listing = models.ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    price = variant.get_price(
        product, [], channel_USD, channel_listing, discounts=[discount_info]
    )
    assert price == Money("5.00", "USD")


def test_digital_product_view(client, digital_content_url):
    """Ensure a user (anonymous or not) can download a non-expired digital good
    using its associated token and that all associated events
    are correctly generated."""

    url = digital_content_url.get_absolute_url()
    response = client.get(url)
    filename = os.path.basename(digital_content_url.content.content_file.name)

    assert response.status_code == 200
    assert response["content-type"] == "image/jpeg"
    assert response["content-disposition"] == 'attachment; filename="%s"' % filename

    # Ensure an event was generated from downloading a digital good.
    # The validity of this event is checked in test_digital_product_increment_download
    assert account_events.CustomerEvent.objects.exists()


@pytest.mark.parametrize(
    "is_user_null, is_line_null", ((False, False), (False, True), (True, True))
)
def test_digital_product_increment_download(
    client,
    customer_user,
    digital_content_url: DigitalContentUrl,
    is_user_null,
    is_line_null,
):
    """Ensure downloading a digital good is possible without it
    being associated to an order line/user."""

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
    digital_content_url = DigitalContentUrl.objects.create(content=digital_content)

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
        digital_content_url = DigitalContentUrl.objects.create(content=digital_content)

    url = digital_content_url.get_absolute_url()
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "price, cost", [(Money("0", "USD"), Money("1", "USD")), (Money("2", "USD"), None)]
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


@patch("saleor.product.thumbnails.create_thumbnails")
def test_create_product_thumbnails(mock_create_thumbnails, product_with_image):
    product_image = product_with_image.media.first()
    create_product_thumbnails(product_image.pk)
    assert mock_create_thumbnails.call_count == 1
    args, kwargs = mock_create_thumbnails.call_args
    assert kwargs == {
        "model": models.ProductMedia,
        "pk": product_image.pk,
        "size_set": "products",
    }
