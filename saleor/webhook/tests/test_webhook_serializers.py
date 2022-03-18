from operator import itemgetter
from unittest.mock import ANY

import graphene
import pytest

from ...attribute.models import AttributeValue
from ...attribute.utils import associate_attribute_values_to_instance
from ...core.prices import quantize_price
from ..serializers import (
    serialize_checkout_lines,
    serialize_product_or_variant_attributes,
)


@pytest.mark.parametrize("taxes_calculated", [True, False])
def test_serialize_checkout_lines(
    checkout_with_items_for_cc, taxes_calculated, site_settings
):
    # given
    checkout = checkout_with_items_for_cc
    channel = checkout.channel
    checkout_lines = list(
        checkout.lines.prefetch_related(
            "variant__product__collections",
            "variant__channel_listings__channel",
            "variant__product__product_type",
        )
    )

    # when
    checkout_lines_data = serialize_checkout_lines(checkout)

    # then
    checkout_with_items_for_cc.refresh_from_db()
    data_len = 0
    for data, line in zip(checkout_lines_data, checkout_lines):
        variant = line.variant
        product = variant.product
        collections = list(product.collections.all())
        variant_channel_listing = None

        for channel_listing in line.variant.channel_listings.all():
            if channel_listing.channel_id == checkout.channel_id:
                variant_channel_listing = channel_listing

        if not variant_channel_listing:
            continue

        base_price = variant.get_price(
            product, collections, channel, variant_channel_listing
        )
        currency = checkout.currency
        assert data == {
            "sku": variant.sku,
            "quantity": line.quantity,
            "base_price": str(quantize_price(base_price.amount, currency)),
            "currency": channel.currency_code,
            "full_name": variant.display_product(),
            "product_name": product.name,
            "variant_name": variant.name,
            "attributes": serialize_product_or_variant_attributes(variant),
            "variant_id": variant.get_global_id(),
        }
        data_len += 1
    assert len(checkout_lines_data) == data_len


def test_serialize_product_attributes(
    product_with_variant_with_two_attributes,
    product_with_multiple_values_attributes,
    product_type_page_reference_attribute,
    page,
):
    variant_data = serialize_product_or_variant_attributes(
        product_with_variant_with_two_attributes.variants.first()
    )

    product_type = product_with_multiple_values_attributes.product_type
    product_type.product_attributes.add(product_type_page_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page.title,
        slug=f"{product_with_multiple_values_attributes.pk}_{page.pk}",
        reference_page=page,
    )
    associate_attribute_values_to_instance(
        product_with_multiple_values_attributes,
        product_type_page_reference_attribute,
        attr_value,
    )
    product_data = serialize_product_or_variant_attributes(
        product_with_multiple_values_attributes
    )
    assert len(variant_data) == 2
    assert variant_data[1] == {
        "entity_type": None,
        "id": ANY,
        "input_type": "dropdown",
        "name": "Size",
        "slug": "size",
        "unit": None,
        "values": [
            {
                "file": None,
                "name": "Small",
                "reference": None,
                "rich_text": None,
                "date_time": None,
                "date": None,
                "boolean": None,
                "slug": "small",
                "value": "",
            }
        ],
    }

    assert len(product_data) == 2
    assert product_data[0]["name"] == "Available Modes"
    assert sorted(product_data[0]["values"], key=itemgetter("name")) == [
        {
            "name": "Eco Mode",
            "slug": "eco",
            "file": None,
            "reference": None,
            "rich_text": None,
            "date_time": None,
            "date": None,
            "boolean": None,
            "value": "",
        },
        {
            "name": "Performance Mode",
            "slug": "power",
            "file": None,
            "reference": None,
            "rich_text": None,
            "date_time": None,
            "date": None,
            "boolean": None,
            "value": "",
        },
    ]
    assert product_data[1]["name"] == "Page reference"
    assert sorted(product_data[1]["values"], key=itemgetter("name")) == [
        {
            "name": "Test page",
            "slug": attr_value.slug,
            "file": None,
            "reference": graphene.Node.to_global_id(
                attr_value.attribute.entity_type, page.pk
            ),
            "rich_text": None,
            "date_time": None,
            "date": None,
            "boolean": None,
            "value": "",
        },
    ]
