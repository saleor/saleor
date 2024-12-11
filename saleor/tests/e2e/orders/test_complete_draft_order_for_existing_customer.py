import pytest

from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..users.utils import create_customer
from ..utils import assign_permissions
from .utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
)


@pytest.mark.e2e
def test_complete_draft_order_for_existing_customer_CORE_0237(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_users,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_users,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    product_price = 10

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    _product_id, product_variant_id, _product_variant_price = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        product_price,
    )

    customer_address = {
        "city": "Fort Wayne",
        "cityArea": "",
        "companyName": "",
        "country": "US",
        "countryArea": "Indiana",
        "firstName": "Charles",
        "lastName": "Hembree",
        "phone": "12136399632",
        "postalCode": "46802",
        "streetAddress1": "1183 Cessna Drive",
        "streetAddress2": "",
    }
    customer_input = {
        "email": "new3@com.com",
        "firstName": "Charles",
        "lastName": "Hembree",
        "note": "Important customer",
        "defaultBillingAddress": customer_address,
        "defaultShippingAddress": customer_address,
    }

    user_data = create_customer(
        e2e_staff_api_client,
        customer_input,
    )
    user_id = user_data["id"]
    user_email = user_data["email"]

    # Step 1 - Create draft order
    draft_order_input = {
        "channelId": channel_id,
        "user": user_id,
        "shippingAddress": customer_address,
        "billingAddress": customer_address,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        draft_order_input,
    )
    order_id = data["order"]["id"]
    assert order_id is not None
    assert data["order"]["status"] == "DRAFT"
    assert data["order"]["user"]["id"] == user_id
    assert data["order"]["user"]["email"] == user_email
    assert (
        data["order"]["shippingAddress"]["streetAddress1"]
        == customer_address["streetAddress1"]
    )
    assert (
        data["order"]["billingAddress"]["streetAddress1"]
        == customer_address["streetAddress1"]
    )

    # Step 2 - Add lines to the order
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        }
    ]
    order_lines = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_product_variant_id = order_lines["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id == product_variant_id

    # Step 3 - Update order's shipping method
    input = {"shippingMethod": shipping_method_id}
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_shipping_id = draft_order["order"]["deliveryMethod"]["id"]
    assert order_shipping_id is not None

    # Step 4 - Complete the order and check it's status
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    order = order["order"]
    assert order["user"]["id"] == user_id
    assert order["user"]["email"] == user_email
    assert order["status"] == "UNFULFILLED"
