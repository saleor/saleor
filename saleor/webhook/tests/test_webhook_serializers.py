from unittest.mock import ANY, sentinel

import graphene
import pytest

from ...attribute import AttributeEntityType, AttributeInputType, AttributeType
from ...attribute.models import Attribute, AttributeValue
from ...attribute.utils import associate_attribute_values_to_instance
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.prices import quantize_price
from ...discount.utils.checkout import (
    create_or_update_discount_objects_from_promotion_for_checkout,
)
from ...plugins.manager import get_plugins_manager
from ..serializers import (
    serialize_checkout_lines,
    serialize_product_attributes,
    serialize_variant_attributes,
    serialize_variant_full_name,
)


def test_serialize_variant_attributes(product_with_variant_with_two_attributes):
    variant_data = serialize_variant_attributes(
        product_with_variant_with_two_attributes.variants.first()
    )
    assert len(variant_data) == 2
    assert {
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
    } in variant_data


def test_serialize_product_attributes(
    product,
    product_type,
    product_type_product_reference_attribute,
    product_type_page_reference_attribute,
    file_attribute,
    page,
):
    # given
    multiselect_name = "Available Modes"
    attribute = Attribute.objects.create(
        slug="modes",
        name=multiselect_name,
        input_type=AttributeInputType.MULTISELECT,
        type=AttributeType.PRODUCT_TYPE,
    )
    product_type.product_attributes.set(
        [
            attribute,
            product_type_product_reference_attribute,
            product_type_page_reference_attribute,
            file_attribute,
        ]
    )

    # multiselect
    attr_val_1 = AttributeValue.objects.create(
        attribute=attribute, name="Eco Mode", slug="eco"
    )
    associate_attribute_values_to_instance(product, {attribute.id: [attr_val_1]})

    # product reference
    product_slug = f"{product.pk}"
    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product.name,
        slug=product_slug,
        reference_product=product,
    )
    associate_attribute_values_to_instance(
        product, {product_type_product_reference_attribute.id: [attr_value]}
    )

    # page reference
    page_slug = f"{page.pk}"
    ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        reference_page=page,
        slug=page_slug,
        name=page.title,
        date_time=None,
    )
    associate_attribute_values_to_instance(
        product, {product_type_page_reference_attribute.id: [ref_value]}
    )

    # file
    file_attr_value = file_attribute.values.first()
    associate_attribute_values_to_instance(
        product, {file_attribute.id: [file_attr_value]}
    )

    # when
    product_data = serialize_product_attributes(product)

    # then
    assert len(product_data) == 4
    for data in product_data:
        if data["name"] == multiselect_name:
            assert data["values"] == [
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
            ]
            continue

        if data["name"] == product_type_product_reference_attribute.name:
            assert data["values"] == [
                {
                    "name": product.name,
                    "slug": product_slug,
                    "file": None,
                    "reference": graphene.Node.to_global_id(
                        AttributeEntityType.PRODUCT, product.pk
                    ),
                    "rich_text": None,
                    "date_time": None,
                    "date": None,
                    "boolean": None,
                    "value": "",
                },
            ]
            continue

        if data["name"] == product_type_page_reference_attribute.name:
            assert data["values"] == [
                {
                    "name": page.title,
                    "slug": page_slug,
                    "file": None,
                    "reference": graphene.Node.to_global_id(
                        AttributeEntityType.PAGE, page.pk
                    ),
                    "rich_text": None,
                    "date_time": None,
                    "date": None,
                    "boolean": None,
                    "value": "",
                },
            ]
            continue

        if data["name"] == file_attribute.name:
            assert data["values"] == [
                {
                    "name": file_attr_value.name,
                    "slug": file_attr_value.slug,
                    "file": {
                        "content_type": file_attr_value.content_type,
                        "file_url": file_attr_value.file_url,
                    },
                    "reference": None,
                    "rich_text": None,
                    "date_time": None,
                    "date": None,
                    "boolean": None,
                    "value": "",
                },
            ]
            continue


ATTRIBUTES = sentinel.ATTRIBUTES


@pytest.mark.parametrize("taxes_calculated", [True, False])
def test_serialize_checkout_lines(
    checkout_with_items_for_cc, taxes_calculated, site_settings
):
    # given
    checkout = checkout_with_items_for_cc
    channel = checkout.channel
    checkout_lines, _ = fetch_checkout_lines(checkout, prefetch_variant_attributes=True)

    # when
    checkout_lines_data = serialize_checkout_lines(checkout)

    # then
    checkout_with_items_for_cc.refresh_from_db()
    for data, line_info in zip(checkout_lines_data, checkout_lines, strict=False):
        variant = line_info.line.variant
        product = variant.product
        variant_channel_listing = line_info.channel_listing

        base_price = variant.get_price(variant_channel_listing)
        currency = checkout.currency
        assert data == {
            "sku": variant.sku,
            "quantity": line_info.line.quantity,
            "base_price": str(quantize_price(base_price.amount, currency)),
            "currency": channel.currency_code,
            "full_name": serialize_variant_full_name(variant),
            "product_name": product.name,
            "variant_name": variant.name,
            "attributes": serialize_variant_attributes(variant),
            "variant_id": variant.get_global_id(),
        }
    assert len(checkout_lines_data) == len(list(checkout_lines))


def test_serialize_checkout_lines_with_promotion(checkout_with_item_on_promotion):
    # given
    checkout = checkout_with_item_on_promotion
    channel = checkout.channel
    checkout_lines, _ = fetch_checkout_lines(checkout, prefetch_variant_attributes=True)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)
    variant = checkout_lines[0].variant

    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines
    )

    # when
    checkout_lines_data = serialize_checkout_lines(checkout)

    # then
    checkout.refresh_from_db()
    assert len(checkout_lines) == 1
    for data, line_info in zip(checkout_lines_data, checkout_lines, strict=False):
        variant = line_info.line.variant
        product = variant.product
        variant_channel_listing = line_info.channel_listing

        base_price = variant.get_price(variant_channel_listing)
        undiscounted_base_price = variant.get_base_price(variant_channel_listing)
        currency = checkout.currency
        assert base_price < undiscounted_base_price
        assert data == {
            "sku": variant.sku,
            "quantity": line_info.line.quantity,
            "base_price": str(quantize_price(base_price.amount, currency)),
            "currency": channel.currency_code,
            "full_name": serialize_variant_full_name(variant),
            "product_name": product.name,
            "variant_name": variant.name,
            "attributes": serialize_variant_attributes(variant),
            "variant_id": variant.get_global_id(),
        }
    assert len(checkout_lines_data) == len(list(checkout_lines))
