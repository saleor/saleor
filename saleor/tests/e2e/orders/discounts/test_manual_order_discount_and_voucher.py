from decimal import Decimal

import pytest

from .....core.prices import quantize_price
from .....discount import DiscountType, DiscountValueType
from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ...vouchers.utils import create_voucher, create_voucher_channel_listing
from ..utils import draft_order_create, draft_order_update, order_discount_add
from ..utils.order_discount_delete import order_discount_delete


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
    usage_limit,
    single_use,
    apply_once_per_order,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
        "usageLimit": usage_limit,
        "singleUse": single_use,
        "applyOncePerOrder": apply_once_per_order,
    }
    voucher_data = create_voucher(e2e_staff_api_client, input)

    voucher_id = voucher_data["id"]
    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": voucher_discount_value,
        },
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_code, voucher_id, voucher_discount_value


@pytest.mark.e2e
def test_manual_order_discount_with_entire_order_voucher_CORE_0940(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "prices_entered_with_tax": False,
    }
    shipping_base_price = Decimal(10)
    currency = "USD"
    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "Inpost",
                                "add_channels": {"price": shipping_base_price},
                            }
                        ],
                    },
                ],
                "order_settings": {
                    "includeDraftOrderInVoucherUsage": True,
                },
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    tax_rate = Decimal("1.1")
    update_country_tax_rates(
        e2e_staff_api_client,
        "US",
        [{"rate": (tax_rate - 1) * 100}],
    )

    variant_price = Decimal(20)
    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=variant_price
    )

    # Step 1 - Create draft order
    quantity = 2
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": shipping_method_id,
        "userEmail": "test_user@test.com",
        "lines": [{"variantId": product_variant_id, "quantity": quantity}],
    }
    data = draft_order_create(e2e_staff_api_client, input)
    undiscounted_line_total = quantize_price(variant_price * quantity, currency)
    undiscounted_total = undiscounted_line_total + shipping_base_price

    order_data = data["order"]
    order_id = order_data["id"]
    assert not order_data["discounts"]
    assert order_data["shippingPrice"]["net"]["amount"] == shipping_base_price
    assert order_data["shippingPrice"]["gross"]["amount"] == quantize_price(
        shipping_base_price * tax_rate, currency
    )
    assert order_data["total"]["net"]["amount"] == undiscounted_total
    assert order_data["total"]["gross"]["amount"] == quantize_price(
        undiscounted_total * tax_rate, currency
    )
    assert len(order_data["lines"]) == 1
    line_data = order_data["lines"][0]
    assert line_data["unitPrice"]["net"]["amount"] == variant_price
    assert line_data["unitPrice"]["gross"]["amount"] == quantize_price(
        variant_price * tax_rate, currency
    )
    assert line_data["totalPrice"]["net"]["amount"] == undiscounted_line_total
    assert line_data["totalPrice"]["gross"]["amount"] == quantize_price(
        undiscounted_line_total * tax_rate, currency
    )

    # Step 2 - Add entire order voucher
    voucher_discount_amount = Decimal(10)
    voucher_code, voucher_id, voucher_discount_value = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="code-123",
        voucher_discount_type="FIXED",
        voucher_discount_value=voucher_discount_amount,
        voucher_type="ENTIRE_ORDER",
        usage_limit=10,
        single_use=False,
        apply_once_per_order=False,
    )
    data = draft_order_update(
        e2e_staff_api_client, order_id, {"voucherCode": voucher_code}
    )
    order_data = data["order"]
    assert len(order_data["discounts"]) == 1
    voucher_discount_data = order_data["discounts"][0]
    assert voucher_discount_data["type"] == DiscountType.VOUCHER.upper()
    assert voucher_discount_data["value"] == voucher_discount_value
    assert voucher_discount_data["valueType"] == DiscountValueType.FIXED.upper()
    assert voucher_discount_data["reason"] == f"Voucher code: {voucher_code}"
    assert voucher_discount_data["amount"]["amount"] == voucher_discount_amount

    expected_total = undiscounted_total - voucher_discount_amount
    expected_line_total = undiscounted_line_total - voucher_discount_amount
    expected_unit_price = quantize_price(expected_line_total / quantity, currency)

    assert order_data["shippingPrice"]["net"]["amount"] == shipping_base_price
    assert order_data["shippingPrice"]["gross"]["amount"] == quantize_price(
        shipping_base_price * tax_rate, currency
    )
    assert order_data["total"]["net"]["amount"] == expected_total
    assert order_data["total"]["gross"]["amount"] == quantize_price(
        expected_total * tax_rate, currency
    )
    assert len(order_data["lines"]) == 1
    line_data = order_data["lines"][0]
    assert line_data["unitPrice"]["net"]["amount"] == expected_unit_price
    assert line_data["unitPrice"]["gross"]["amount"] == quantize_price(
        expected_unit_price * tax_rate, currency
    )
    assert line_data["totalPrice"]["net"]["amount"] == expected_line_total
    assert line_data["totalPrice"]["gross"]["amount"] == quantize_price(
        expected_line_total * tax_rate, currency
    )

    assert order_data["voucher"]["codes"]["totalCount"] == 1
    assert order_data["voucher"]["codes"]["edges"][0]["node"]["code"] == voucher_code
    assert order_data["voucher"]["codes"]["edges"][0]["node"]["used"] == 1

    # Step 3 - Add manual order discount
    # Manual discount should override voucher
    manual_discount_amount = Decimal(20)
    manual_discount_reason = "Staff discount"
    data = order_discount_add(
        e2e_staff_api_client,
        order_id,
        {
            "valueType": DiscountValueType.FIXED.upper(),
            "value": manual_discount_amount,
            "reason": manual_discount_reason,
        },
    )

    order_data = data["order"]
    assert len(order_data["discounts"]) == 1
    manual_discount_data = order_data["discounts"][0]
    manual_discount_id = manual_discount_data["id"]
    assert manual_discount_data["type"] == DiscountType.MANUAL.upper()
    assert manual_discount_data["value"] == manual_discount_amount
    assert manual_discount_data["valueType"] == DiscountValueType.FIXED.upper()
    assert manual_discount_data["reason"] == manual_discount_reason
    assert manual_discount_data["amount"]["amount"] == manual_discount_amount

    subtotal_discount_portion = quantize_price(
        undiscounted_line_total / undiscounted_total * manual_discount_amount, currency
    )
    shipping_discount_portion = manual_discount_amount - subtotal_discount_portion

    expected_total = undiscounted_total - manual_discount_amount
    expected_shipping_price = shipping_base_price - shipping_discount_portion
    expected_line_total = undiscounted_line_total - subtotal_discount_portion
    expected_unit_price = quantize_price(expected_line_total / quantity, currency)

    assert order_data["shippingPrice"]["net"]["amount"] == expected_shipping_price
    assert quantize_price(
        Decimal(order_data["shippingPrice"]["gross"]["amount"]), currency
    ) == quantize_price(expected_shipping_price * tax_rate, currency)
    assert order_data["total"]["net"]["amount"] == expected_total
    assert order_data["total"]["gross"]["amount"] == quantize_price(
        expected_total * tax_rate, currency
    )
    assert len(order_data["lines"]) == 1
    line_data = order_data["lines"][0]
    assert line_data["unitPrice"]["net"]["amount"] == expected_unit_price
    assert quantize_price(
        Decimal(line_data["unitPrice"]["gross"]["amount"]), currency
    ) == quantize_price(expected_unit_price * tax_rate, currency)
    assert line_data["totalPrice"]["net"]["amount"] == expected_line_total
    assert quantize_price(
        Decimal(line_data["totalPrice"]["gross"]["amount"]), currency
    ) == quantize_price(expected_line_total * tax_rate, currency)

    # Manual discount overrides voucher's discount, but don't disconnect it
    # from the order. The code usage shouldn't be reduced
    assert order_data["voucherCode"] == voucher_code
    assert order_data["voucher"]["codes"]["totalCount"] == 1
    assert order_data["voucher"]["codes"]["edges"][0]["node"]["code"] == voucher_code
    assert order_data["voucher"]["codes"]["edges"][0]["node"]["used"] == 1

    # Step 4 - Delete manual order discount
    # Voucher should be applied back
    data = order_discount_delete(e2e_staff_api_client, manual_discount_id)

    order_data = data["order"]
    assert len(order_data["discounts"]) == 1
    voucher_discount_data = order_data["discounts"][0]
    assert voucher_discount_data["type"] == DiscountType.VOUCHER.upper()
    assert voucher_discount_data["value"] == voucher_discount_value
    assert voucher_discount_data["valueType"] == DiscountValueType.FIXED.upper()
    assert voucher_discount_data["reason"] == f"Voucher code: {voucher_code}"
    assert voucher_discount_data["amount"]["amount"] == voucher_discount_amount

    expected_total = undiscounted_total - voucher_discount_amount
    expected_line_total = undiscounted_line_total - voucher_discount_amount
    expected_unit_price = quantize_price(expected_line_total / quantity, currency)

    assert order_data["shippingPrice"]["net"]["amount"] == shipping_base_price
    assert order_data["shippingPrice"]["gross"]["amount"] == quantize_price(
        shipping_base_price * tax_rate, currency
    )
    assert order_data["total"]["net"]["amount"] == expected_total
    assert order_data["total"]["gross"]["amount"] == quantize_price(
        expected_total * tax_rate, currency
    )
    assert len(order_data["lines"]) == 1
    line_data = order_data["lines"][0]
    assert line_data["unitPrice"]["net"]["amount"] == expected_unit_price
    assert line_data["unitPrice"]["gross"]["amount"] == quantize_price(
        expected_unit_price * tax_rate, currency
    )
    assert line_data["totalPrice"]["net"]["amount"] == expected_line_total
    assert line_data["totalPrice"]["gross"]["amount"] == quantize_price(
        expected_line_total * tax_rate, currency
    )

    assert order_data["voucherCode"] == voucher_code
    assert order_data["voucher"]["codes"]["totalCount"] == 1
    assert order_data["voucher"]["codes"]["edges"][0]["node"]["code"] == voucher_code
    assert order_data["voucher"]["codes"]["edges"][0]["node"]["used"] == 1
