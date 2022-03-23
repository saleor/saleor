from operator import itemgetter
from unittest.mock import ANY, Mock, patch, sentinel

import graphene
import pytest

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.prices import quantize_price
from ...plugins.manager import get_plugins_manager
from ..serializers import (
    get_base_price,
    serialize_checkout_lines_with_taxes,
    serialize_checkout_lines_without_taxes,
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
    # =======
    # @pytest.mark.parametrize(
    #     "taxes_included, taxes_calculated",
    #     [
    #         (True, True),
    #         (True, False),
    #         (False, True),
    #         (False, False),
    #     ],
    # >>>>>>> upstream/taxes-by-sync-webhooks
)
def test_serialize_checkout_lines_with_taxes(
    checkout_with_prices,
    mocked_fetch_checkout,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    # =======
    #     site_settings.include_taxes_in_prices = taxes_included
    #     site_settings.save()
    #     checkout = checkout_with_items_for_cc
    #     channel = checkout.channel
    #     lines, _ = fetch_checkout_lines(checkout, prefetch_variant_attributes=True)
    #
    #     checkout_lines = [line_info.line for line_info in lines]
    #
    #     for line in checkout_lines:
    #         line.currency = channel.currency_code
    #         line.unit_price_net_amount = Decimal("10.00")
    #         line.unit_price_gross_amount = (
    #             Decimal("12.30") if taxes_calculated else Decimal("10.00")
    #         )
    #
    #     CheckoutLine.objects.bulk_update(
    #         checkout_lines,
    #         fields=[
    #             "currency",
    #             "unit_price_net_amount",
    #             "unit_price_gross_amount",
    #         ],
    #     )
    # >>>>>>> upstream/taxes-by-sync-webhooks

    # when
    checkout_lines_data = serialize_checkout_lines_with_taxes(
        checkout_info, manager, lines, []
    )

    # then
    for data, line_info in zip(checkout_lines_data, lines):
        line = line_info.line
        variant = line.variant
        product = variant.product
        collections = line_info.collections
        variant_channel_listing = line_info.channel_listing
        base_price = variant.get_price(
            product, collections, checkout.channel, variant_channel_listing
        )
        currency = checkout.currency
        assert data == {
            "id": graphene.Node.to_global_id("CheckoutLine", line.pk),
            "sku": variant.sku,
            "quantity": line.quantity,
            "charge_taxes": product.charge_taxes,
            "base_price": str(quantize_price(base_price.amount, currency)),
            "price_net_amount": str(
                quantize_price(line.unit_price_net_amount, currency)
            ),
            "price_gross_amount": str(
                quantize_price(line.unit_price_gross_amount, currency)
            ),
            "price_with_discounts_net_amount": str(
                quantize_price(line.unit_price_with_discounts_net_amount, currency)
            ),
            "price_with_discounts_gross_amount": str(
                quantize_price(line.unit_price_with_discounts_gross_amount, currency)
            ),
            "currency": checkout.channel.currency_code,
            "full_name": variant.display_product(),
            "product_name": product.name,
            "variant_name": variant.name,
            "attributes": ANY,
            "variant_id": ANY,
            "product_metadata": product.metadata,
            "product_type_metadata": product.product_type.metadata,
        }

    assert len(checkout_lines_data) == len(list(lines))
    mocked_fetch_checkout.assert_called()


@patch(
    "saleor.webhook.serializers.serialize_product_or_variant_attributes",
    new=Mock(return_value=ATTRIBUTES),
)
@pytest.mark.parametrize("taxes_included", [True, False])
def test_serialize_checkout_lines_without_taxes(
    checkout_with_prices,
    mocked_fetch_checkout,
    taxes_included,
    site_settings,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    site_settings.include_taxes_in_prices = taxes_included
    site_settings.save()

    # when
    checkout_lines_data = serialize_checkout_lines_without_taxes(
        checkout, lines, taxes_included
    )

    # then
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
        base_price_with_discounts = get_base_price(
            line.unit_price_with_discounts, taxes_included
        )
        currency = checkout.currency
        assert data == {
            "id": graphene.Node.to_global_id("CheckoutLine", line.pk),
            "sku": variant.sku,
            "quantity": line.quantity,
            "charge_taxes": product.charge_taxes,
            "base_price": str(quantize_price(base_price.amount, currency)),
            "base_price_with_discounts": str(
                quantize_price(base_price_with_discounts, currency)
            ),
            "currency": checkout.channel.currency_code,
            "full_name": variant.display_product(),
            "product_name": product.name,
            "variant_name": variant.name,
            "attributes": ANY,
            "variant_id": ANY,
            "product_metadata": product.metadata,
            "product_type_metadata": product.product_type.metadata,
        }
    assert len(checkout_lines_data) == len(list(lines))


# def test_serialize_product_attributes(
#     product_with_variant_with_two_attributes,
#     product_with_multiple_values_attributes,
#     product_type_page_reference_attribute,
#     page,
# ):
#     variant_data = serialize_product_or_variant_attributes(
#         product_with_variant_with_two_attributes.variants.first()
#     )
#
#     product_type = product_with_multiple_values_attributes.product_type
#     product_type.product_attributes.add(product_type_page_reference_attribute)
#     attr_value = AttributeValue.objects.create(
#         attribute=product_type_page_reference_attribute,
#         name=page.title,
#         slug=f"{product_with_multiple_values_attributes.pk}_{page.pk}",
#         reference_page=page,
#     )
#     associate_attribute_values_to_instance(
#         product_with_multiple_values_attributes,
#         product_type_page_reference_attribute,
#         attr_value,
#     )
#     product_data = serialize_product_or_variant_attributes(
#         product_with_multiple_values_attributes
#     )
#     assert len(variant_data) == 2
#     assert variant_data[1] == {
#         "entity_type": None,
#         "id": ANY,
#         "input_type": "dropdown",
#         "name": "Size",
#         "slug": "size",
#         "unit": None,
#         "values": [
#             {
#                 "file": None,
#                 "name": "Small",
#                 "reference": None,
#                 "rich_text": None,
#                 "date_time": None,
#                 "date": None,
#                 "boolean": None,
#                 "slug": "small",
#                 "value": "",
#             }
#         ],
#     }
#
#     assert len(product_data) == 2
#     assert product_data[0]["name"] == "Available Modes"
#     assert sorted(product_data[0]["values"], key=itemgetter("name")) == [
#         {
#             "name": "Eco Mode",
#             "slug": "eco",
#             "file": None,
#             "reference": None,
#             "rich_text": None,
#             "date_time": None,
#             "date": None,
#             "boolean": None,
#             "value": "",
#         },
#         {
#             "name": "Performance Mode",
#             "slug": "power",
#             "file": None,
#             "reference": None,
#             "rich_text": None,
#             "date_time": None,
#             "date": None,
#             "boolean": None,
#             "value": "",
#         },
#     ]
#     assert product_data[1]["name"] == "Page reference"
#     assert sorted(product_data[1]["values"], key=itemgetter("name")) == [
#         {
#             "name": "Test page",
#             "slug": attr_value.slug,
#             "file": None,
#             "reference": graphene.Node.to_global_id(
#                 attr_value.attribute.entity_type, page.pk
#             ),
#             "rich_text": None,
#             "date_time": None,
#             "date": None,
#             "boolean": None,
#             "value": "",
#         },
#     ]
# >>>>>>> upstream/taxes-by-sync-webhooks
