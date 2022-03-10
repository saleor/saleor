from operator import itemgetter
from unittest.mock import ANY, Mock, patch, sentinel

import graphene
import pytest

from ...checkout.fetch import fetch_checkout_lines
from ...core.prices import quantize_price
from ..serializers import (
    serialize_checkout_lines,
    serialize_product_or_variant_attributes,
)


def test_serialize_product_attributes(
    product_with_variant_with_two_attributes, product_with_multiple_values_attributes
):
    variant_data = serialize_product_or_variant_attributes(
        product_with_variant_with_two_attributes.variants.first()
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

    assert len(product_data) == 1
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


ATTRIBUTES = sentinel.ATTRIBUTES


@patch(
    "saleor.webhook.serializers.serialize_product_or_variant_attributes",
    new=Mock(return_value=ATTRIBUTES),
)
@pytest.mark.parametrize("taxes_included", [True, False])
def test_serialize_checkout_lines(
    # mocked_fetch,
    checkout_with_items_for_cc,
    taxes_included,
    site_settings,
):
    # given
    lines, _ = fetch_checkout_lines(checkout_with_items_for_cc)
    site_settings.include_taxes_in_prices = taxes_included
    site_settings.save()
    checkout = checkout_with_items_for_cc

    # when
    checkout_lines_data = serialize_checkout_lines(
        checkout, lines, Mock(return_value={})
    )

    # then
    checkout_with_items_for_cc.refresh_from_db()
    data_len = 0
    for data, line_info in zip(checkout_lines_data, lines):
        line = line_info.line
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
            product, collections, checkout.channel, variant_channel_listing
        )
        currency = checkout.currency
        assert data["id"] == graphene.Node.to_global_id("CheckoutLine", line.pk)
        assert data["sku"] == variant.sku
        assert data["quantity"] == line.quantity
        assert data["charge_taxes"] == product.charge_taxes
        assert data["base_price"] == quantize_price(base_price.amount, currency)
        assert data["currency"] == checkout_with_items_for_cc.channel.currency_code
        assert data["full_name"] == variant.display_product()
        assert data["product_name"] == product.name
        assert data["variant_name"] == variant.name
        assert data["attributes"] == ATTRIBUTES
        assert data["variant_id"]
        assert data["product_metadata"] == product.metadata
        assert data["product_type_metadata"] == product.product_type.metadata
        data_len += 1

    assert len(checkout_lines_data) == data_len
