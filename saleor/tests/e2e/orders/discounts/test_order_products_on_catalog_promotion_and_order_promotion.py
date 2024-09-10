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
from ..utils import (
    draft_order_complete,
    draft_order_create,
    order_line_update,
    order_lines_create,
    order_update_shipping,
)


def prepare_product_and_catalog_promotion(
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


def prepare_order_promotion(
    e2e_staff_api_client,
    channel_id,
    discount_value,
    discount_type,
    order_predicate_total_value,
):
    promotion_name = "Black Friday Subtotal Promotion"
    promotion_type = "ORDER"

    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type
    )
    promotion_id = promotion_data["id"]
    order_predicate = {
        "discountedObjectPredicate": {
            "baseTotalPrice": {"range": {"gte": order_predicate_total_value}}
        }
    }

    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": "test rule",
        "orderPredicate": order_predicate,
        "rewardType": "SUBTOTAL_DISCOUNT",
        "rewardValue": discount_value,
        "rewardValueType": discount_type,
    }
    create_promotion_rule(e2e_staff_api_client, input)

    return promotion_id


@pytest.mark.e2e
def test_draft_order_products_on_catalog_promotion_and_order_promotion_CORE_2132(
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
    product1_variant_price = 60
    product2_variant_price = 150
    catalog_promotion_value = 20
    catalog_promotion_type = "PERCENTAGE"
    country_tax_rate = 10
    country = "US"
    order_promotion_value = 25
    order_promotion_discount_type = "PERCENTAGE"
    order_promotion_total_predicate = 500

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

    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": country_tax_rate}],
    )

    # Create 2 products on catalog promotion
    (
        product_variant_id_1,
        product_variant_id_2,
        catalog_promotion_id,
    ) = prepare_product_and_catalog_promotion(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price_1=product1_variant_price,
        variant_price_2=product2_variant_price,
        promotion_name="Summer Sale",
        discount_value=catalog_promotion_value,
        discount_type=catalog_promotion_type,
        promotion_rule_name="rule for Accessories",
    )

    # Prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Create order promotion

    order_promotion_id = prepare_order_promotion(
        e2e_staff_api_client,
        channel_id,
        discount_value=order_promotion_value,
        discount_type=order_promotion_discount_type,
        order_predicate_total_value=order_promotion_total_predicate,
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
        {"variantId": product_variant_id_1, "quantity": 1},
        {"variantId": product_variant_id_2, "quantity": 1},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_line1 = order["order"]["lines"][0]
    order_line2 = order["order"]["lines"][1]

    # Assert lines:
    expected_product1_unit_gross_price = round(
        product1_variant_price
        - (product1_variant_price * (catalog_promotion_value / 100)),
        2,
    )
    expected_product1_unit_tax_price = round(
        (expected_product1_unit_gross_price * country_tax_rate)
        / (100 + country_tax_rate),
        2,
    )
    assert order_line1["variant"]["id"] == product_variant_id_1
    assert order_line1["unitDiscountReason"] == f"Promotion: {catalog_promotion_id}"
    assert order_line1["unitDiscountValue"] == catalog_promotion_value
    assert order_line1["unitDiscountType"] == "PERCENTAGE"
    assert order_line1["unitDiscount"]["amount"] == round(
        product1_variant_price * (catalog_promotion_value / 100), 2
    )
    assert (
        order_line1["unitPrice"]["gross"]["amount"]
        == expected_product1_unit_gross_price
    )
    assert order_line1["unitPrice"]["tax"]["amount"] == expected_product1_unit_tax_price
    assert (
        order_line1["unitPrice"]["gross"]["amount"]
        != order_line1["undiscountedUnitPrice"]["gross"]["amount"]
    )

    expected_product2_unit_gross_price = round(
        product2_variant_price
        - (product2_variant_price * (catalog_promotion_value / 100)),
        2,
    )
    expected_product2_unit_tax_price = round(
        (expected_product2_unit_gross_price * country_tax_rate)
        / (100 + country_tax_rate),
        2,
    )
    assert order_line2["variant"]["id"] == product_variant_id_2
    assert order_line2["unitDiscountReason"] == f"Promotion: {catalog_promotion_id}"
    assert order_line2["unitDiscountValue"] == catalog_promotion_value
    assert order_line2["unitDiscountType"] == "PERCENTAGE"
    assert order_line2["unitDiscount"]["amount"] == round(
        product2_variant_price * (catalog_promotion_value / 100), 2
    )
    assert (
        order_line2["unitPrice"]["gross"]["amount"]
        == expected_product2_unit_gross_price
    )
    assert order_line2["unitPrice"]["tax"]["amount"] == expected_product2_unit_tax_price
    assert (
        order_line2["unitPrice"]["gross"]["amount"]
        != order_line2["undiscountedUnitPrice"]["gross"]["amount"]
    )

    # Assert subtotal:
    subtotal_gross = round(
        (expected_product1_unit_gross_price + expected_product2_unit_gross_price), 2
    )
    assert order["order"]["subtotal"]["gross"]["amount"] == subtotal_gross
    subtotal_tax = round(
        (subtotal_gross * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["order"]["subtotal"]["tax"]["amount"] == subtotal_tax

    # Step 3 - Update quantity for fist product
    input = {"quantity": 5}
    order_line_update(e2e_staff_api_client, order_line1["id"], input)

    # Step 4 - Update quantity for second product
    input = {"quantity": 3}
    order = order_line_update(e2e_staff_api_client, order_line2["id"], input)

    # Assert undiscounted total is over 500$
    undiscounted_total_before_shipping = order["order"]["undiscountedTotal"]["gross"][
        "amount"
    ]
    assert undiscounted_total_before_shipping > order_promotion_total_predicate

    # Assert discounts
    assert order["order"]["discounts"][0]["type"] == "ORDER_PROMOTION"
    assert order["order"]["discounts"][0]["value"] == order_promotion_value
    assert (
        order["order"]["discounts"][0]["reason"] == f"Promotion: {order_promotion_id}"
    )

    expected_subtotal_without_order_promotion = round(
        (expected_product1_unit_gross_price * 5)
        + (expected_product2_unit_gross_price * 3),
        2,
    )
    expected_order_promotion_discount = round(
        expected_subtotal_without_order_promotion * (order_promotion_value / 100), 2
    )
    assert (
        order["order"]["discounts"][0]["amount"]["amount"]
        == expected_order_promotion_discount
    )

    # Assert subtotal
    expected_subtotal_gross = round(
        expected_subtotal_without_order_promotion - expected_order_promotion_discount, 2
    )
    assert order["order"]["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    expected_subtotal_tax = round(
        (expected_subtotal_gross * country_tax_rate) / (100 + country_tax_rate), 2
    )
    assert order["order"]["subtotal"]["tax"]["amount"] == expected_subtotal_tax

    # Step 5 - Add shipping method
    input = {"shippingMethod": shipping_method_id}
    order = order_update_shipping(e2e_staff_api_client, order_id, input)
    order = order["order"]
    assert order["deliveryMethod"]["id"] is not None

    # Assert shipping price
    assert order["shippingPrice"]["gross"]["amount"] == shipping_price
    expected_shipping_tax = round(
        (shipping_price * country_tax_rate) / (100 + country_tax_rate),
        2,
    )
    assert order["shippingPrice"]["tax"]["amount"] == expected_shipping_tax

    # Assert subtotal is the same as before adding shipping method
    assert order["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    assert order["subtotal"]["tax"]["amount"] == expected_subtotal_tax

    # Assert total after adding shipping method
    expected_total_gross = round(expected_subtotal_gross + shipping_price, 2)
    assert order["total"]["gross"]["amount"] == expected_total_gross
    expected_total_tax = round(expected_subtotal_tax + expected_shipping_tax, 2)
    assert order["total"]["tax"]["amount"] == expected_total_tax

    # Assert undiscounted total
    expected_undiscounted_total_gross = round(
        (product1_variant_price * 5) + (product2_variant_price * 3) + shipping_price, 2
    )
    assert (
        order["undiscountedTotal"]["gross"]["amount"]
        == expected_undiscounted_total_gross
    )
    expected_undiscounted_total_tax = round(
        (expected_undiscounted_total_gross * country_tax_rate)
        / (100 + country_tax_rate),
        2,
    )
    assert (
        order["undiscountedTotal"]["tax"]["amount"] == expected_undiscounted_total_tax
    )

    # Step 6 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    completed_order = order["order"]
    assert completed_order["status"] == "UNFULFILLED"
    assert completed_order["total"]["gross"]["amount"] == expected_total_gross
    assert completed_order["total"]["tax"]["amount"] == expected_total_tax
    assert completed_order["subtotal"]["gross"]["amount"] == expected_subtotal_gross
    assert completed_order["subtotal"]["tax"]["amount"] == expected_subtotal_tax
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
    assert line1["unitDiscountReason"] == f"Promotion: {catalog_promotion_id}"
    line2 = completed_order["lines"][1]
    assert line2["unitDiscountReason"] == f"Promotion: {catalog_promotion_id}"
    assert completed_order["discounts"][0]["type"] == "ORDER_PROMOTION"
