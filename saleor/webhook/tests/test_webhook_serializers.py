from decimal import Decimal
from operator import itemgetter
from unittest.mock import ANY, patch

import graphene
import pytest

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.models import CheckoutLine
from ...core.prices import quantize_price
from ...plugins.manager import get_plugins_manager
from ..payloads import (
    _get_line_prices_data_with_taxes,
    _get_line_prices_data_without_taxes,
)
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


@patch("saleor.checkout.calculations.fetch_checkout_prices_if_expired")
@pytest.mark.parametrize(
    "get_unit_price, tax_webhook_called",
    [
        (lambda c, m, ls, l: _get_line_prices_data_without_taxes(c.checkout, l), False),
        (lambda c, m, ls, l: _get_line_prices_data_with_taxes(c, m, ls, l), True),
    ],
)
@pytest.mark.parametrize(
    "taxes_included, taxes_calculated",
    [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ],
)
def test_serialize_checkout_lines(
    mocked_fetch,
    checkout_with_items_for_cc,
    taxes_included,
    taxes_calculated,
    site_settings,
    get_unit_price,
    tax_webhook_called,
):
    # given
    mocked_fetch.side_effect = (
        lambda checkout_info, manager, lines, address, discounts: (checkout_info, lines)
    )
    lines, _ = fetch_checkout_lines(checkout_with_items_for_cc)
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout_with_items_for_cc, lines, [], manager)
    site_settings.include_taxes_in_prices = taxes_included
    site_settings.save()
    checkout = checkout_with_items_for_cc
    channel = checkout.channel
    for line_info in lines:
        line = line_info.line
        line.unit_price_net_amount = Decimal("10.00")
        if not taxes_calculated:
            line.unit_price_gross_amount = Decimal("10.00")
        else:
            line.unit_price_gross_amount = Decimal("12.30")

    CheckoutLine.objects.bulk_update(
        [line_info.line for line_info in lines],
        fields=[
            "currency",
            "unit_price_net_amount",
            "unit_price_gross_amount",
        ],
    )

    # when
    checkout_lines_data = serialize_checkout_lines(
        checkout,
        lines,
        lambda line_info: get_unit_price(checkout_info, manager, lines, line_info),
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
            product, collections, channel, variant_channel_listing
        )
        currency = checkout.currency
        print(data)
        assert data == {
            "id": graphene.Node.to_global_id("CheckoutLine", line.pk),
            "sku": variant.sku,
            "quantity": line.quantity,
            "charge_taxes": product.charge_taxes,
            "base_price": quantize_price(base_price.amount, currency),
            **get_unit_price(checkout_info, manager, lines, line_info),
            "currency": channel.currency_code,
            "full_name": variant.display_product(),
            "product_name": product.name,
            "variant_name": variant.name,
            "attributes": ANY,
            "variant_id": ANY,
            "product_metadata": product.metadata,
            "product_type_metadata": product.product_type.metadata,
        }
        data_len += 1
    assert len(checkout_lines_data) == data_len
    assert bool(mocked_fetch.call_count) is tax_webhook_called
