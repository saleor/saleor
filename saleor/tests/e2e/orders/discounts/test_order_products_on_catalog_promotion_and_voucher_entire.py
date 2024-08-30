import pytest

from .....product.tasks import recalculate_discounted_price_for_products_task
from ... import DEFAULT_ADDRESS
from ...product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ...vouchers.utils import (
    create_voucher,
    create_voucher_channel_listing,
)
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
    order_update_shipping,
)


def prepare_product_and_promotion(
    e2e_staff_api_client,
    warehouse_id,
    channel_id,
    variant_price_1,
    variant_price_2,
    promotion_name,
    discount_value,
    discount_type,
    promotion_rule_name,
):
    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(
        e2e_staff_api_client,
    )
    category_id = category_data["id"]
    category_ids = [category_id]

    product_data_1 = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id_1 = product_data_1["id"]
    create_product_channel_listing(e2e_staff_api_client, product_id_1, channel_id)

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    variant_data_1 = create_product_variant(
        e2e_staff_api_client, product_id_1, stocks=stocks
    )
    product_variant_id_1 = variant_data_1["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id_1,
        channel_id,
        variant_price_1,
    )
    product_data_2 = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id_2 = product_data_2["id"]
    create_product_channel_listing(e2e_staff_api_client, product_id_2, channel_id)

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    variant_data_2 = create_product_variant(
        e2e_staff_api_client, product_id_2, stocks=stocks
    )
    product_variant_id_2 = variant_data_2["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id_2,
        channel_id,
        variant_price_2,
    )

    promotion_type = "CATALOGUE"
    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type
    )
    promotion_id = promotion_data["id"]

    catalogue_predicate = {
        "categoryPredicate": {"ids": category_ids},
    }
    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
        "cataloguePredicate": catalogue_predicate,
        "rewardValue": discount_value,
        "rewardValueType": discount_type,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    category_predicate = promotion_rule["cataloguePredicate"]["categoryPredicate"][
        "ids"
    ]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert category_predicate[0] == category_id

    return (
        product_variant_id_1,
        product_variant_id_2,
        promotion_id,
    )


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
        "singleUse": True,
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

    return voucher_code, voucher_discount_value


@pytest.mark.e2e
def test_order_products_on_catalog_promotion_and_voucher_entire_order_CORE_2131(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shipping_price = 10
    product1_variant_price = 33.33
    product2_variant_price = 113.50
    catalog_promotion_value = 30

    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "display_gross_prices": False,
        "prices_entered_with_tax": True,
    }

    # Create channel, warehouse, shipping method and update tax configuration
    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "us shipping zone",
                                "add_channels": {
                                    "price": shipping_price,
                                },
                            }
                        ],
                    }
                ],
                "order_settings": {
                    "automaticallyConfirmAllNewOrders": True,
                    "allowUnpaidOrders": False,
                    "includeDraftOrderInVoucherUsage": False,
                },
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]
    country_tax_rate = 10
    country = "US"

    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": country_tax_rate}],
    )

    # Create 2 products on catalog promotion
    (
        product_variant_id_1,
        product_variant_id_2,
        promotion_id,
    ) = prepare_product_and_promotion(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price_1=product1_variant_price,
        variant_price_2=product2_variant_price,
        promotion_name="Summer Sale",
        discount_value=catalog_promotion_value,
        discount_type="PERCENTAGE",
        promotion_rule_name="rule for Accessories",
    )

    # Prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Create voucher entire order
    voucher_code, voucher_discount_value = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="voucher15",
        voucher_discount_type="PERCENTAGE",
        voucher_discount_value=15,
        voucher_type="ENTIRE_ORDER",
    )

    # Step 1 - Create a draft order for a product with fixed promotion
    input = {
        "channelId": channel_id,
        "userEmail": "customer@example.com",
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 2 - Add order lines to the order
    lines = [
        {"variantId": product_variant_id_1, "quantity": 2},
        {"variantId": product_variant_id_2, "quantity": 2},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_product1_variant_id = order["order"]["lines"][0]
    order_product2_variant_id = order["order"]["lines"][1]

    # Assert lines:
    expected_product1_unit_price = round(
        product1_variant_price
        - (product1_variant_price * (catalog_promotion_value / 100)),
        2,
    )
    assert order_product1_variant_id["variant"]["id"] == product_variant_id_1
    assert (
        order_product1_variant_id["unitDiscountReason"] == f"Promotion: {promotion_id}"
    )
    assert order_product1_variant_id["unitDiscountValue"] == catalog_promotion_value
    assert order_product1_variant_id["unitDiscountType"] == "PERCENTAGE"
    assert order_product1_variant_id["unitDiscount"]["amount"] == round(
        product1_variant_price * (catalog_promotion_value / 100), 2
    )
    assert (
        order_product1_variant_id["unitPrice"]["gross"]["amount"]
        == expected_product1_unit_price
    )
    assert (
        order_product1_variant_id["unitPrice"]["gross"]["amount"]
        != order_product1_variant_id["undiscountedUnitPrice"]["gross"]["amount"]
    )

    expected_product2_unit_price = round(
        product2_variant_price
        - (product2_variant_price * (catalog_promotion_value / 100)),
        2,
    )
    assert order_product2_variant_id["variant"]["id"] == product_variant_id_2
    assert (
        order_product2_variant_id["unitDiscountReason"] == f"Promotion: {promotion_id}"
    )
    assert order_product2_variant_id["unitDiscountValue"] == catalog_promotion_value
    assert order_product2_variant_id["unitDiscountType"] == "PERCENTAGE"
    assert order_product2_variant_id["unitDiscount"]["amount"] == round(
        product2_variant_price * (catalog_promotion_value / 100), 2
    )
    assert (
        order_product2_variant_id["unitPrice"]["gross"]["amount"]
        == expected_product2_unit_price
    )
    assert (
        order_product2_variant_id["unitPrice"]["gross"]["amount"]
        != order_product2_variant_id["undiscountedUnitPrice"]["gross"]["amount"]
    )

    # Assert subtotal:
    expected_subtotal_gross = round(
        (expected_product1_unit_price * 2 + expected_product2_unit_price * 2), 2
    )
    assert order["order"]["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    expected_subtotal_tax = round(
        (expected_subtotal_gross * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["order"]["subtotal"]["tax"]["amount"] == expected_subtotal_tax

    # Step 3 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    order = order_update_shipping(e2e_staff_api_client, order_id, input)
    assert order["order"]["deliveryMethod"]["id"] is not None

    # Assert shipping price
    assert order["order"]["shippingPrice"]["gross"]["amount"] == shipping_price
    expected_shipping_tax = round(
        (shipping_price * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["order"]["shippingPrice"]["tax"]["amount"] == expected_shipping_tax

    # Assert subtotal is the same as before adding shipping method
    assert order["order"]["subtotal"]["gross"]["amount"] == expected_subtotal_gross

    # Assert total after adding shipping method
    expected_total_gross = round(expected_subtotal_gross + shipping_price, 2)
    assert order["order"]["total"]["gross"]["amount"] == expected_total_gross
    expected_total_tax = round(expected_subtotal_tax + expected_shipping_tax, 2)
    assert order["order"]["total"]["tax"]["amount"] == expected_total_tax

    # Assert undiscounted total
    expected_undiscounted_total_gross = round(
        (product1_variant_price * 2) + (product2_variant_price * 2) + shipping_price, 2
    )
    assert (
        order["order"]["undiscountedTotal"]["gross"]["amount"]
        == expected_undiscounted_total_gross
    )
    expected_undiscounted_total_tax = round(
        (expected_undiscounted_total_gross * country_tax_rate)
        / (100 + country_tax_rate),
        2,
    )
    assert (
        order["order"]["undiscountedTotal"]["tax"]["amount"]
        == expected_undiscounted_total_tax
    )

    # Step 4 - Add voucher entire order
    order = draft_order_update(
        e2e_staff_api_client, order_id, {"voucherCode": voucher_code}
    )
    # Assert voucher
    assert order["order"]["voucherCode"] == voucher_code
    assert order["order"]["discounts"][0]["type"] == "VOUCHER"
    assert order["order"]["discounts"][0]["value"] == voucher_discount_value
    assert order["order"]["discounts"][0]["amount"]["amount"] == round(
        expected_subtotal_gross * (voucher_discount_value / 100), 2
    )

    # Assert subtotal with voucher
    subtotal_gross_with_voucher = round(
        expected_subtotal_gross * (1 - (voucher_discount_value / 100)), 2
    )
    assert order["order"]["subtotal"]["gross"]["amount"] == subtotal_gross_with_voucher
    subtotal_tax_with_voucher = round(
        (subtotal_gross_with_voucher * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["order"]["subtotal"]["tax"]["amount"] == subtotal_tax_with_voucher

    # Assert shipping price is the same
    assert order["order"]["shippingPrice"]["gross"]["amount"] == shipping_price
    assert order["order"]["shippingPrice"]["tax"]["amount"] == expected_shipping_tax
    assert order["order"]["undiscountedShippingPrice"]["amount"] == shipping_price

    # Assert total with voucher
    total_gross_with_voucher = round(
        subtotal_gross_with_voucher + shipping_price,
        2,
    )
    assert order["order"]["total"]["gross"]["amount"] == total_gross_with_voucher
    total_tax_with_voucher = round(
        (total_gross_with_voucher * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["order"]["total"]["tax"]["amount"] == total_tax_with_voucher

    # Step 5 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    completed_order = order["order"]
    assert completed_order["status"] == "UNFULFILLED"
    assert completed_order["total"]["gross"]["amount"] == total_gross_with_voucher
    assert completed_order["total"]["tax"]["amount"] == total_tax_with_voucher
    assert completed_order["subtotal"]["gross"]["amount"] == subtotal_gross_with_voucher
    assert completed_order["subtotal"]["tax"]["amount"] == subtotal_tax_with_voucher
    assert completed_order["shippingPrice"]["gross"]["amount"] == shipping_price
    assert completed_order["shippingPrice"]["tax"]["amount"] == expected_shipping_tax
    assert (
        completed_order["undiscountedTotal"]["gross"]["amount"]
        == expected_undiscounted_total_gross
    )
    assert (
        completed_order["undiscountedTotal"]["tax"]["amount"]
        == expected_undiscounted_total_tax
    )
    line1 = completed_order["lines"][0]
    assert line1["unitDiscountReason"] == f"Promotion: {promotion_id}"
    assert line1["unitDiscount"]["amount"] == round(
        product1_variant_price * (catalog_promotion_value / 100), 2
    )
    line2 = completed_order["lines"][1]
    assert line2["unitDiscountReason"] == f"Promotion: {promotion_id}"
    assert line2["unitDiscount"]["amount"] == round(
        product2_variant_price * (catalog_promotion_value / 100), 2
    )
