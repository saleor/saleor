import datetime
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import graphene
from prices import Money

from ..attribute import AttributeEntityType, AttributeInputType
from ..checkout.fetch import fetch_checkout_lines
from ..core.prices import quantize_price
from ..product.models import Product

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from ..checkout.models import Checkout
    from ..product.models import ProductVariant


def serialize_variant_full_name(
    variant: "ProductVariant", product: Product | None = None
) -> str:
    if product:
        assert product.id == variant.product_id, (
            "Product does not belong to provided variant."
        )
    else:
        product = variant.product

    variant_display = str(variant)
    product_display = (
        f"{product} ({variant_display})" if variant_display else str(product)
    )
    return product_display


def serialize_checkout_lines(checkout: "Checkout") -> list[dict]:
    data = []
    channel = checkout.channel
    currency = channel.currency_code
    lines, _ = fetch_checkout_lines(checkout, prefetch_variant_attributes=True)
    for line_info in lines:
        variant = line_info.variant
        product = variant.product
        base_price = line_info.undiscounted_unit_price
        total_discount_amount_for_line = sum(
            [discount.amount_value for discount in line_info.get_promotion_discounts()],
            Decimal(0),
        )
        if total_discount_amount_for_line:
            unit_discount_amount = (
                total_discount_amount_for_line / line_info.line.quantity
            )
            unit_discount = Money(unit_discount_amount, currency)
            unit_discount = quantize_price(unit_discount, currency)
            base_price -= unit_discount
        data.append(
            {
                "sku": variant.sku,
                "variant_id": variant.get_global_id(),
                "quantity": line_info.line.quantity,
                "base_price": str(quantize_price(base_price.amount, currency)),
                "currency": currency,
                "full_name": serialize_variant_full_name(variant),
                "product_name": product.name,
                "variant_name": variant.name,
                "attributes": serialize_variant_attributes(variant),
            }
        )
    return data


def serialize_product_attributes(product: "Product") -> list[dict]:
    data = []

    def _prepare_reference(attribute, attr_value) -> None | str:
        if attribute.input_type != AttributeInputType.REFERENCE:
            return None
        if attribute.entity_type == AttributeEntityType.PAGE:
            reference_pk = attr_value.reference_page_id
        elif attribute.entity_type == AttributeEntityType.PRODUCT:
            reference_pk = attr_value.reference_product_id
        else:
            return None

        reference_id = graphene.Node.to_global_id(attribute.entity_type, reference_pk)
        return reference_id

    attribute_products = product.product_type.attributeproduct.all()
    assigned_values = product.attributevalues.all()

    values_map = defaultdict(list)
    for av in assigned_values:
        values_map[av.value.attribute_id].append(av.value)

    for attribute_product in attribute_products:
        attribute = attribute_product.attribute

        attr_id = graphene.Node.to_global_id("Attribute", attribute.pk)
        attr_data: dict[Any, Any] = {
            "name": attribute.name,
            "input_type": attribute.input_type,
            "slug": attribute.slug,
            "entity_type": attribute.entity_type,
            "unit": attribute.unit,
            "id": attr_id,
            "values": [],
        }

        for attr_value in values_map[attribute.pk]:
            attr_slug = attr_value.slug
            value: dict[
                str,
                str | datetime.datetime | datetime.date | bool | dict[str, Any] | None,
            ] = {
                "name": attr_value.name,
                "slug": attr_slug,
                "value": attr_value.value,
                "rich_text": attr_value.rich_text,
                "boolean": attr_value.boolean,
                "date_time": attr_value.date_time,
                "date": attr_value.date_time,
                "reference": _prepare_reference(attribute, attr_value),
                "file": None,
            }

            if attr_value.file_url:
                value["file"] = {
                    "content_type": attr_value.content_type,
                    "file_url": attr_value.file_url,
                }
            attr_data["values"].append(value)

        data.append(attr_data)

    return data


def serialize_variant_attributes(variant: "ProductVariant") -> list[dict]:
    data = []

    def _prepare_reference(attribute, attr_value) -> None | str:
        if attribute.input_type != AttributeInputType.REFERENCE:
            return None
        if attribute.entity_type == AttributeEntityType.PAGE:
            reference_pk = attr_value.reference_page_id
        elif attribute.entity_type == AttributeEntityType.PRODUCT:
            reference_pk = attr_value.reference_product_id
        else:
            return None

        reference_id = graphene.Node.to_global_id(attribute.entity_type, reference_pk)
        return reference_id

    for attr in variant.attributes.all():
        attr_id = graphene.Node.to_global_id("Attribute", attr.assignment.attribute_id)
        attribute = attr.assignment.attribute
        attr_data: dict[Any, Any] = {
            "name": attribute.name,
            "input_type": attribute.input_type,
            "slug": attribute.slug,
            "entity_type": attribute.entity_type,
            "unit": attribute.unit,
            "id": attr_id,
            "values": [],
        }

        for attr_value in attr.values.all():
            attr_slug = attr_value.slug
            value: dict[
                str,
                str | datetime.datetime | datetime.date | bool | dict[str, Any] | None,
            ] = {
                "name": attr_value.name,
                "slug": attr_slug,
                "value": attr_value.value,
                "rich_text": attr_value.rich_text,
                "boolean": attr_value.boolean,
                "date_time": attr_value.date_time,
                "date": attr_value.date_time,
                "reference": _prepare_reference(attribute, attr_value),
                "file": None,
            }

            if attr_value.file_url:
                value["file"] = {
                    "content_type": attr_value.content_type,
                    "file_url": attr_value.file_url,
                }
            attr_data["values"].append(value)

        data.append(attr_data)

    return data
