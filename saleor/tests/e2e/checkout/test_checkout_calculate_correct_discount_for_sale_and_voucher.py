import pytest

from ..channel.utils import create_channel
from ..product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
from ..sales.utils import create_sale, create_sale_channel_listing, sale_catalogues_add
from ..shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ..utils import assign_permissions
from ..vouchers.utils import create_voucher, create_voucher_channel_listing
from ..warehouse.utils import create_warehouse
from .utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_lines_add,
)


@pytest.mark.e2e
def test_checkout_calculate_discount_for_sale_and_voucher_1014(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before
    channel_slug = "test-channel"

    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    warehouse_ids = [warehouse_id]

    channel_data = create_channel(
        e2e_staff_api_client,
        warehouse_ids,
        slug=channel_slug,
    )
    channel_id = channel_data["id"]
    channel_ids = [channel_id]

    shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=warehouse_ids,
        channel_ids=channel_ids,
    )
    shipping_zone_id = shipping_zone_data["id"]

    shipping_method_data = create_shipping_method(
        e2e_staff_api_client, shipping_zone_id
    )
    shipping_method_id = shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client, shipping_method_id, channel_id
    )
    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(
        e2e_staff_api_client,
    )
    category_id = category_data["id"]

    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id = product_data["id"]
    create_product_channel_listing(e2e_staff_api_client, product_id, channel_id)

    stocks = [
        {
            "warehouse": warehouse_data["id"],
            "quantity": 5,
        }
    ]
    variant_data = create_product_variant(
        e2e_staff_api_client, product_id, stocks=stocks
    )
    product_variant_id = variant_data["id"]

    variant_price = "30.0"
    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        variant_price,
    )
    sale_name = "Sale Fixed"
    sale_discount_type = "FIXED"
    sale_discount_value = 5
    sale = create_sale(e2e_staff_api_client, sale_name, sale_discount_type)
    sale_id = sale["id"]
    sale_listing_input = [
        {
            "channelId": channel_id,
            "discountValue": sale_discount_value,
        }
    ]
    create_sale_channel_listing(
        e2e_staff_api_client, sale_id, add_channels=sale_listing_input
    )
    catalogue_input = {"variants": [product_variant_id]}
    sale_catalogues_add(e2e_staff_api_client, sale_id, catalogue_input)
    voucher_code = "VOUCHER001"
    voucher_discount_value = "30"

    voucher_data = create_voucher(
        e2e_staff_api_client,
        "PERCENTAGE",
        voucher_code,
        "ENTIRE_ORDER",
    )
    voucher_id = voucher_data["id"]
    # assert voucher_data["discountValueType"] == "PERCENTAGE"

    channel_listing = [
        {"channelId": channel_id, "discountValue": voucher_discount_value}
    ]
    voucher_listing_data = create_voucher_channel_listing(
        e2e_staff_api_client, voucher_id, channel_listing
    )
    assert voucher_listing_data["channelListings"][0]["channel"]["id"] == channel_id
    assert voucher_listing_data["channelListings"][0]["discountValue"] == float(
        voucher_discount_value
    )

    # Step 1 - checkoutCreate for product on sale
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]
    checkout_lines = checkout_data["lines"][0]
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]
    unit_price_on_sale = float(variant_price) - sale_discount_value

    assert checkout_data["isShippingRequired"] is True
    assert checkout_lines["unitPrice"]["gross"]["amount"] == unit_price_on_sale
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == float(variant_price)

    # Step 2 checkoutAddPromoCode
    voucher_discount = unit_price_on_sale * float(voucher_discount_value) / 100
    unit_price_sale_and_variant = unit_price_on_sale - voucher_discount
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )
    assert checkout_data["discount"]["amount"] == voucher_discount
    assert (
        checkout_data["lines"][0]["unitPrice"]["gross"]["amount"]
        == unit_price_sale_and_variant
    )

    # Step 3 checkoutLinesAdd
    lines_add = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_lines_add(e2e_staff_api_client, checkout_id, lines_add)
    checkout_lines = checkout_data["lines"][0]
    assert checkout_lines["quantity"] == 2
    assert checkout_lines["totalPrice"]["gross"]["amount"] == float(
        2 * unit_price_sale_and_variant
    )

    # Step 4 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    # subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]

    # Step 5 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client, checkout_id, total_gross_amount
    )

    # Step 6 - Complete checkout.
    order_data = checkout_complete(e2e_not_logged_api_client, checkout_id)

    _order_line = order_data["lines"][0]
    assert order_data["status"] == "UNFULFILLED"
    # assert order_data["total"]["gross"]["amount"] == total_gross_amount
    # assert order_data["subtotal"]["gross"]["amount"] == subtotal_gross_amount
    # assert order_line["undiscountedUnitPrice"]["gross"]["amount"] == float(
    #     variant_price
    # )
    # assert order_line["unitDiscountType"] == "FIXED"
    # assert order_line["unitPrice"]["gross"]["amount"] == unit_price
    # assert order_line["unitDiscount"]["amount"] == float(sale_discount_value)
    # assert order_line["unitDiscountReason"] == f"Sale: {sale_id}"
