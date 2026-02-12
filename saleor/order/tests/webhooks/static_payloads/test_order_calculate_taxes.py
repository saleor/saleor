import datetime
import json
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from freezegun import freeze_time

from .....core.prices import quantize_price
from .....discount import DiscountType, DiscountValueType, VoucherType
from ....webhooks.order_calculate_taxes import (
    generate_order_payload_for_tax_calculation,
)


@pytest.fixture
def order_for_payload(fulfilled_order, voucher_percentage):
    order = fulfilled_order

    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal(20),
        amount_value=Decimal("33.0"),
        reason="Discount from staff",
    )
    discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal(10),
        amount_value=Decimal("16.5"),
        name="Voucher",
        voucher=voucher_percentage,
    )

    discount.created_at = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(
        days=1
    )
    discount.save(update_fields=["created_at"])

    line_without_sku = order.lines.last()
    line_without_sku.product_sku = None
    line_without_sku.save()

    return order


@freeze_time()
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_order_payload_for_tax_calculation(
    order_for_payload,
    prices_entered_with_tax,
):
    # given
    order = order_for_payload

    tax_configuration = order.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    discount_1, discount_2 = list(order.discounts.all())
    user = order.user

    # when
    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]

    # then
    currency = order.currency

    assert payload == {
        "type": "Order",
        "id": graphene.Node.to_global_id("Order", order.id),
        "channel": {
            "id": graphene.Node.to_global_id("Channel", order.channel_id),
            "type": "Channel",
            "slug": order.channel.slug,
            "currency_code": order.channel.currency_code,
        },
        "address": {
            "id": graphene.Node.to_global_id("Address", order.shipping_address_id),
            "type": "Address",
            "first_name": order.shipping_address.first_name,
            "last_name": order.shipping_address.last_name,
            "company_name": order.shipping_address.company_name,
            "street_address_1": order.shipping_address.street_address_1,
            "street_address_2": order.shipping_address.street_address_2,
            "city": order.shipping_address.city,
            "city_area": order.shipping_address.city_area,
            "postal_code": order.shipping_address.postal_code,
            "country": order.shipping_address.country.code,
            "country_area": order.shipping_address.country_area,
            "phone": str(order.shipping_address.phone),
        },
        "user_id": graphene.Node.to_global_id("User", user.pk),
        "user_public_metadata": user.metadata,
        "included_taxes_in_prices": prices_entered_with_tax,
        "currency": order.currency,
        "shipping_name": order.shipping_method.name,
        "shipping_amount": str(
            quantize_price(order.base_shipping_price_amount, currency)
        ),
        "metadata": order.metadata,
        "discounts": [
            {
                "name": discount_1.name,
                "amount": str(quantize_price(discount_1.amount_value, currency)),
            },
            {
                "name": discount_2.name,
                "amount": str(quantize_price(discount_2.amount_value, currency)),
            },
        ],
        "lines": [
            {
                "type": "OrderLine",
                "id": graphene.Node.to_global_id("OrderLine", line.id),
                "product_name": line.product_name,
                "variant_name": line.variant_name,
                "quantity": line.quantity,
                "variant_id": line.product_variant_id,
                "full_name": line.variant.display_product() if line.variant else None,
                "product_metadata": (
                    line.variant.product.metadata if line.variant else {}
                ),
                "product_type_metadata": (
                    line.variant.product.product_type.metadata if line.variant else {}
                ),
                "charge_taxes": True,
                "sku": line.product_sku,
                "unit_amount": str(
                    quantize_price(line.base_unit_price_amount, line.currency)
                ),
                "total_amount": str(
                    quantize_price(
                        line.base_unit_price_amount * line.quantity, line.currency
                    )
                ),
            }
            for line in order.lines.all()
        ],
    }


@freeze_time()
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
@patch(
    "saleor.order.webhooks.order_calculate_taxes._generate_order_lines_payload_for_tax_calculation"
)
def test_generate_order_payload_for_tax_calculation_entire_order_voucher(
    mocked_order_lines, order_for_payload, prices_entered_with_tax, voucher
):
    # given
    order = order_for_payload

    tax_configuration = order.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    order_lines = '"order_lines"'
    mocked_order_lines.return_value = order_lines

    discount_1, discount_2 = list(order.discounts.all())
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.apply_once_per_order = False
    voucher.save()
    discount_2.voucher = voucher
    discount_2.save()
    user = order.user

    # when
    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]

    # then
    currency = order.currency

    assert payload == {
        "type": "Order",
        "id": graphene.Node.to_global_id("Order", order.id),
        "channel": {
            "id": graphene.Node.to_global_id("Channel", order.channel_id),
            "type": "Channel",
            "slug": order.channel.slug,
            "currency_code": order.channel.currency_code,
        },
        "address": {
            "id": graphene.Node.to_global_id("Address", order.shipping_address_id),
            "type": "Address",
            "first_name": order.shipping_address.first_name,
            "last_name": order.shipping_address.last_name,
            "company_name": order.shipping_address.company_name,
            "street_address_1": order.shipping_address.street_address_1,
            "street_address_2": order.shipping_address.street_address_2,
            "city": order.shipping_address.city,
            "city_area": order.shipping_address.city_area,
            "postal_code": order.shipping_address.postal_code,
            "country": order.shipping_address.country.code,
            "country_area": order.shipping_address.country_area,
            "phone": str(order.shipping_address.phone),
        },
        "user_id": graphene.Node.to_global_id("User", user.pk),
        "user_public_metadata": user.metadata,
        "included_taxes_in_prices": prices_entered_with_tax,
        "currency": order.currency,
        "shipping_name": order.shipping_method.name,
        "shipping_amount": str(
            quantize_price(order.base_shipping_price_amount, currency)
        ),
        "metadata": order.metadata,
        "discounts": [
            {
                "name": discount_1.name,
                "amount": str(quantize_price(discount_1.amount_value, currency)),
            },
            {
                "name": discount_2.name,
                "amount": str(quantize_price(discount_2.amount_value, currency)),
            },
        ],
        "lines": json.loads(order_lines),
    }
    mocked_order_lines.assert_called_once()


@freeze_time()
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_order_payload_for_tax_calculation_line_level_voucher_excluded(
    order_for_payload, prices_entered_with_tax, voucher
):
    # given
    order = order_for_payload

    tax_configuration = order.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])

    discount_1, discount_2 = list(order.discounts.all())
    voucher.type = VoucherType.ENTIRE_ORDER
    # line level vouchers should be excluded from discounts
    voucher.apply_once_per_order = True
    voucher.save()
    discount_2.voucher = voucher
    discount_2.save()

    # when
    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]

    # then
    assert payload["discounts"] == [
        {
            "name": discount_1.name,
            "amount": str(quantize_price(discount_1.amount_value, order.currency)),
        },
    ]


@pytest.mark.parametrize("charge_taxes", [True, False])
def test_order_lines_for_tax_calculation_with_removed_variant(
    order, order_line_with_one_allocation, charge_taxes
):
    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    order.lines.add(order_line_with_one_allocation)
    currency = order.currency
    line = order_line_with_one_allocation
    line.voucher_code = "Voucher001"
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.sale_id = graphene.Node.to_global_id("Sale", 1)
    variant = line.variant
    line.variant = None
    line.save()

    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    assert line_payload == {
        "type": "OrderLine",
        "id": line_id,
        "variant_id": graphene.Node.to_global_id("ProductVariant", variant.id),
        "full_name": None,
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "product_metadata": {},
        "product_type_metadata": {},
        "quantity": line.quantity,
        "sku": line.product_sku,
        "charge_taxes": charge_taxes,
        "unit_amount": str(quantize_price(line.base_unit_price_amount, currency)),
        "total_amount": str(
            quantize_price(line.base_unit_price_amount * line.quantity, currency)
        ),
    }


@pytest.mark.parametrize(
    ("charge_taxes", "prices_entered_with_tax"),
    [(False, False), (False, True), (True, False), (True, True)],
)
def test_order_lines_for_tax_calculation_have_all_required_fields(
    order,
    order_line_with_one_allocation,
    charge_taxes,
    prices_entered_with_tax,
):
    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    order.lines.add(order_line_with_one_allocation)
    currency = order.currency
    line = order_line_with_one_allocation
    line.voucher_code = "Voucher001"
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.sale_id = graphene.Node.to_global_id("Sale", 1)
    line.save()
    variant = line.variant
    product = variant.product
    product_type = product.product_type
    product.metadata = {"product_meta": "value"}
    product.save()
    product_type.metadata = {"product_type_meta": "value"}
    product_type.save()

    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    assert line_payload == {
        "type": "OrderLine",
        "id": line_id,
        "variant_id": graphene.Node.to_global_id("ProductVariant", variant.id),
        "full_name": variant.display_product(),
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "product_metadata": {"product_meta": "value"},
        "product_type_metadata": {"product_type_meta": "value"},
        "quantity": line.quantity,
        "sku": line.product_sku,
        "charge_taxes": charge_taxes,
        "unit_amount": str(quantize_price(line.base_unit_price_amount, currency)),
        "total_amount": str(
            quantize_price(line.base_unit_price_amount * line.quantity, currency)
        ),
    }
