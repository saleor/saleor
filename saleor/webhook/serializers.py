from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional, Union

import graphene
from prices import Money

from ..attribute import AttributeEntityType, AttributeInputType
from ..checkout import base_calculations
from ..checkout.fetch import fetch_checkout_lines
from ..core.prices import quantize_price
from ..product.models import Product
from ..tax.utils import get_charge_taxes_for_checkout

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..checkout.models import Checkout
    from ..product.models import ProductVariant


def serialize_checkout_lines(checkout: "Checkout") -> list[dict]:
    data = []
    channel = checkout.channel
    currency = channel.currency_code
    lines, _ = fetch_checkout_lines(checkout, prefetch_variant_attributes=True)
    for line_info in lines:
        variant = line_info.variant
        channel_listing = line_info.channel_listing
        product = variant.product
        base_price = variant.get_base_price(
            channel_listing, line_info.line.price_override
        )
        total_discount_amount_for_line = Decimal("0")
        total_discount_amount_for_line = sum(
            [discount.amount_value for discount in line_info.get_promotion_discounts()],
            Decimal("0"),
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
                "full_name": variant.display_product(),
                "product_name": product.name,
                "variant_name": variant.name,
                "attributes": serialize_variant_attributes(variant),
            }
        )
    return data


def _get_checkout_line_payload_data(line_info: "CheckoutLineInfo") -> dict[str, Any]:
    line_id = graphene.Node.to_global_id("CheckoutLine", line_info.line.pk)
    variant = line_info.variant
    product = variant.product
    return {
        "id": line_id,
        "sku": variant.sku,
        "variant_id": variant.get_global_id(),
        "quantity": line_info.line.quantity,
        "full_name": variant.display_product(),
        "product_name": product.name,
        "variant_name": variant.name,
        "product_metadata": line_info.product.metadata,
        "product_type_metadata": line_info.product_type.metadata,
    }


def serialize_checkout_lines_for_tax_calculation(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
) -> list[dict]:
    charge_taxes = get_charge_taxes_for_checkout(checkout_info, lines)
    return [
        {
            **_get_checkout_line_payload_data(line_info),
            "charge_taxes": charge_taxes,
            "unit_amount": quantize_price(
                base_calculations.calculate_base_line_unit_price(line_info).amount,
                checkout_info.checkout.currency,
            ),
            "total_amount": quantize_price(
                base_calculations.calculate_base_line_total_price(line_info).amount,
                checkout_info.checkout.currency,
            ),
        }
        for line_info in lines
    ]


def serialize_product_attributes(product: "Product") -> list[dict]:
    data = []

    def _prepare_reference(attribute, attr_value):
        if attribute.input_type != AttributeInputType.REFERENCE:
            return
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
        attribute = attribute_product.attribute  # type: ignore[attr-defined]

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
                str, Optional[Union[str, datetime, date, bool, dict[str, Any]]]
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

    def _prepare_reference(attribute, attr_value):
        if attribute.input_type != AttributeInputType.REFERENCE:
            return
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
                str, Optional[Union[str, datetime, date, bool, dict[str, Any]]]
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
