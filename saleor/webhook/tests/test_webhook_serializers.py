from decimal import Decimal
from unittest.mock import ANY, sentinel

import graphene
import pytest

from ...attribute import AttributeEntityType, AttributeInputType, AttributeType
from ...attribute.models import Attribute, AttributeValue
from ...attribute.utils import associate_attribute_values_to_instance
from ...checkout import base_calculations
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.prices import quantize_price
from ...discount import DiscountType
from ...discount.models import PromotionRule
from ...discount.utils.checkout import (
    create_or_update_discount_objects_from_promotion_for_checkout,
)
from ...plugins.manager import get_plugins_manager
from ...product.models import Product
from ...product.utils.variant_prices import update_discounted_prices_for_promotion
from ...product.utils.variants import fetch_variants_for_promotion_rules
from ..serializers import (
    serialize_checkout_lines,
    serialize_checkout_lines_for_tax_calculation,
    serialize_product_attributes,
    serialize_variant_attributes,
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
    for data, line_info in zip(checkout_lines_data, checkout_lines):
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
            "full_name": variant.display_product(),
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
    for data, line_info in zip(checkout_lines_data, checkout_lines):
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
            "full_name": variant.display_product(),
            "product_name": product.name,
            "variant_name": variant.name,
            "attributes": serialize_variant_attributes(variant),
            "variant_id": variant.get_global_id(),
        }
    assert len(checkout_lines_data) == len(list(checkout_lines))


@pytest.mark.parametrize(
    ("charge_taxes", "prices_entered_with_tax"),
    [(False, False), (False, True), (True, False), (True, True)],
)
def test_serialize_checkout_lines_for_tax_calculation(
    checkout_with_prices, charge_taxes, prices_entered_with_tax
):
    # We should be sure that we always sends base prices to tax app.
    # We shouldn't use previously calculated prices because they can be
    # changed by tax app due to e.g.
    # Checkout discount
    # Propagating shipping tax to lines.

    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    tax_configuration = checkout_info.tax_configuration
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    # when
    checkout_lines_data = serialize_checkout_lines_for_tax_calculation(
        checkout_info, lines
    )

    # then
    for data, line_info in zip(checkout_lines_data, lines):
        line = line_info.line
        variant = line.variant
        product = variant.product

        total_price = base_calculations.calculate_base_line_total_price(
            line_info
        ).amount
        unit_price = base_calculations.calculate_base_line_unit_price(line_info).amount

        assert data == {
            "id": graphene.Node.to_global_id("CheckoutLine", line.pk),
            "sku": variant.sku,
            "quantity": line.quantity,
            "charge_taxes": charge_taxes,
            "full_name": variant.display_product(),
            "product_name": product.name,
            "variant_name": variant.name,
            "variant_id": graphene.Node.to_global_id("ProductVariant", variant.pk),
            "product_metadata": product.metadata,
            "product_type_metadata": product.product_type.metadata,
            "unit_amount": unit_price,
            "total_amount": total_price,
        }
    assert len(checkout_lines_data) == len(list(lines))


def test_serialize_checkout_lines_for_tax_calculation_with_promotion(
    checkout_with_prices, promotion_rule, product_list, product
):
    # given
    checkout = checkout_with_prices
    product_list.append(product)
    promotion_rule.catalogue_predicate = {
        "productPredicate": {
            "ids": [
                graphene.Node.to_global_id("Product", product.id)
                for product in product_list
            ]
        },
    }
    promotion_rule.save(update_fields=["catalogue_predicate"])

    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    update_discounted_prices_for_promotion(Product.objects.all())

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_info, lines)

    tax_configuration = checkout_info.tax_configuration
    tax_configuration.country_exceptions.all().delete()

    # when
    checkout_lines_data = serialize_checkout_lines_for_tax_calculation(
        checkout_info, lines
    )

    # then
    for data, line_info in zip(checkout_lines_data, lines):
        line = line_info.line
        variant = line.variant
        product = variant.product

        total_price = base_calculations.calculate_base_line_total_price(
            line_info
        ).amount
        unit_price = base_calculations.calculate_base_line_unit_price(line_info).amount

        assert data == {
            "id": graphene.Node.to_global_id("CheckoutLine", line.pk),
            "sku": variant.sku,
            "quantity": line.quantity,
            "charge_taxes": tax_configuration.charge_taxes,
            "full_name": variant.display_product(),
            "product_name": product.name,
            "variant_name": variant.name,
            "variant_id": graphene.Node.to_global_id("ProductVariant", variant.pk),
            "product_metadata": product.metadata,
            "product_type_metadata": product.product_type.metadata,
            "unit_amount": unit_price,
            "total_amount": total_price,
        }

        discount = line_info.discounts[0]
        assert discount.type == DiscountType.PROMOTION
        undiscounted_unit_price = variant.get_base_price(
            line_info.channel_listing,
            line_info.line.price_override,
        ).amount
        assert unit_price < undiscounted_unit_price

    assert len(checkout_lines_data) == len(list(lines))


def test_serialize_checkout_lines_for_tax_calculation_with_order_discount(
    checkout_with_item_and_order_discount, product
):
    # given
    checkout = checkout_with_item_and_order_discount

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    tax_configuration = checkout_info.tax_configuration
    tax_configuration.country_exceptions.all().delete()

    # when
    checkout_lines_data = serialize_checkout_lines_for_tax_calculation(
        checkout_info, lines
    )

    # then
    line_info = lines[0]
    line = line_info.line
    variant = line.variant
    product = variant.product

    unit_price = variant.get_price(
        channel_listing=line_info.channel_listing,
    )
    total_price_amount = (unit_price * line.quantity).amount

    line_data = checkout_lines_data[0]
    # the line data shouldn't include order promotion discount
    assert line_data == {
        "id": graphene.Node.to_global_id("CheckoutLine", line.pk),
        "sku": variant.sku,
        "quantity": line.quantity,
        "charge_taxes": tax_configuration.charge_taxes,
        "full_name": variant.display_product(),
        "product_name": product.name,
        "variant_name": variant.name,
        "variant_id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "product_metadata": product.metadata,
        "product_type_metadata": product.product_type.metadata,
        "unit_amount": unit_price.amount,
        "total_amount": total_price_amount,
    }


def test_serialize_checkout_lines_for_tax_calculation_with_gift_promotion(
    checkout_with_item_and_gift_promotion, product
):
    # given
    checkout = checkout_with_item_and_gift_promotion

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    tax_configuration = checkout_info.tax_configuration
    tax_configuration.country_exceptions.all().delete()

    # when
    checkout_lines_data = serialize_checkout_lines_for_tax_calculation(
        checkout_info, lines
    )

    # then
    line_info = [line_info for line_info in lines if not line_info.line.is_gift][0]
    line = line_info.line
    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variant = line.variant
    product = variant.product

    unit_price = variant.get_price(
        channel_listing=line_info.channel_listing,
    )
    total_price_amount = (unit_price * line.quantity).amount

    line_data = [
        line_data for line_data in checkout_lines_data if line_data["id"] == line_id
    ][0]
    assert line_data == {
        "id": line_id,
        "sku": variant.sku,
        "quantity": line.quantity,
        "charge_taxes": tax_configuration.charge_taxes,
        "full_name": variant.display_product(),
        "product_name": product.name,
        "variant_name": variant.name,
        "variant_id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "product_metadata": product.metadata,
        "product_type_metadata": product.product_type.metadata,
        "unit_amount": unit_price.amount,
        "total_amount": total_price_amount,
    }
    gift_info = [line_info for line_info in lines if line_info.line.is_gift][0]
    gift_line = gift_info.line
    gift_line_id = graphene.Node.to_global_id("CheckoutLine", gift_info.line.pk)
    gift_line_data = [
        line_data
        for line_data in checkout_lines_data
        if line_data["id"] == gift_line_id
    ][0]
    assert gift_line_data == {
        "id": gift_line_id,
        "sku": gift_line.variant.sku,
        "quantity": 1,
        "charge_taxes": tax_configuration.charge_taxes,
        "full_name": gift_line.variant.display_product(),
        "product_name": gift_line.variant.product.name,
        "variant_name": gift_line.variant.name,
        "variant_id": graphene.Node.to_global_id(
            "ProductVariant", gift_line.variant.pk
        ),
        "product_metadata": gift_line.variant.product.metadata,
        "product_type_metadata": gift_line.variant.product.product_type.metadata,
        "unit_amount": Decimal("0.00"),
        "total_amount": Decimal("0.00"),
    }
