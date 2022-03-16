from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union

import graphene
from prices import TaxedMoney

from ..attribute import AttributeInputType
from ..checkout import calculations
from ..core.prices import quantize_price
from ..plugins.manager import PluginsManager
from ..product.models import Product

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..checkout.models import Checkout
    from ..discount import DiscountInfo
    from ..product.models import ProductVariant


def get_base_price(price: TaxedMoney, use_gross_as_base_price: bool) -> Decimal:
    if use_gross_as_base_price:
        return price.gross.amount
    return price.net.amount


def _get_checkout_line_payload_data(
    checkout: "Checkout", line_info: "CheckoutLineInfo"
) -> Dict[str, Any]:
    channel = checkout.channel
    currency = channel.currency_code
    line_id = graphene.Node.to_global_id("CheckoutLine", line_info.line.pk)
    variant = line_info.variant
    channel_listing = line_info.channel_listing
    collections = line_info.collections
    product = variant.product
    base_price = variant.get_price(product, collections, channel, channel_listing)

    return {
        "id": line_id,
        "sku": variant.sku,
        "variant_id": variant.get_global_id(),
        "quantity": line_info.line.quantity,
        "charge_taxes": product.charge_taxes,
        "base_price": quantize_price(base_price.amount, currency),
        "currency": currency,
        "full_name": variant.display_product(),
        "product_name": product.name,
        "variant_name": variant.name,
        "attributes": serialize_product_or_variant_attributes(variant),
        "product_metadata": line_info.product.metadata,
        "product_type_metadata": line_info.product_type.metadata,
    }


def serialize_checkout_lines_with_taxes(
    checkout_info: "CheckoutInfo",
    manager: PluginsManager,
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable["DiscountInfo"],
) -> List[dict]:
    data = []
    checkout = checkout_info.checkout
    currency = checkout.currency

    for line_info in lines:
        unit_price_data = calculations.checkout_line_unit_price(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            checkout_line_info=line_info,
            discounts=discounts,
        )
        unit_price = quantize_price(unit_price_data.price_with_sale, currency)
        unit_price_with_discounts = quantize_price(
            unit_price_data.price_with_discounts, currency
        )
        data.append(
            {
                **_get_checkout_line_payload_data(checkout, line_info),
                "price_net_amount": unit_price.net.amount,
                "price_gross_amount": unit_price.gross.amount,
                "price_with_discounts_net_amount": unit_price_with_discounts.net.amount,
                "price_with_discounts_gross_amount": (
                    unit_price_with_discounts.gross.amount
                ),
            }
        )
    return data


def serialize_checkout_lines_without_taxes(
    checkout: "Checkout",
    lines: Iterable["CheckoutLineInfo"],
    use_gross_as_base_price: bool,
) -> List[dict]:
    def untaxed_price_amount(price: TaxedMoney) -> Decimal:
        return quantize_price(
            get_base_price(price, use_gross_as_base_price), checkout.currency
        )

    return [
        {
            **_get_checkout_line_payload_data(checkout, line_info),
            "base_price_with_discounts": untaxed_price_amount(
                line_info.line.unit_price_with_discounts
            ),
        }
        for line_info in lines
    ]


def serialize_product_or_variant_attributes(
    product_or_variant: Union["Product", "ProductVariant"]
) -> List[Dict]:
    data = []

    def _prepare_reference(attribute, attr_slug):
        if attribute.input_type != AttributeInputType.REFERENCE:
            return

        reference_pk = attr_slug.split("_")[1]
        reference_id = graphene.Node.to_global_id(attribute.entity_type, reference_pk)
        return reference_id

    for attr in product_or_variant.attributes.all():
        attr_id = graphene.Node.to_global_id("Attribute", attr.assignment.attribute_id)
        attribute = attr.assignment.attribute
        attr_data: Dict[Any, Any] = {
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
            value: Dict[
                str, Optional[Union[str, datetime, date, bool, Dict[str, Any]]]
            ] = {
                "name": attr_value.name,
                "slug": attr_slug,
                "value": attr_value.value,
                "rich_text": attr_value.rich_text,
                "boolean": attr_value.boolean,
                "date_time": attr_value.date_time,
                "date": attr_value.date_time,
                "reference": _prepare_reference(attribute, attr_slug),
                "file": None,
            }

            if attr_value.file_url:
                value["file"] = {
                    "content_type": attr_value.content_type,
                    "file_url": attr_value.file_url,
                }
            attr_data["values"].append(value)  # type: ignore

        data.append(attr_data)

    return data
