import pytest

from .. import DEFAULT_ADDRESS
from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils.draft_order_complete import raw_draft_order_complete
from .utils.draft_order_create import draft_order_create
from .utils.draft_order_update import draft_order_update
from .utils.order_lines_create import order_lines_create
from .utils.order_query import order_query


@pytest.mark.e2e
def test_cannot_fullfill_order_with_invalid_shipping_method_core_0203(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_shop(
        e2e_staff_api_client,
        shipping_zones=[{"countries": ["US"]}, {"countries": ["PL"]}],
    )

    first_shipping_method_id = shop_data["shipping_methods"][0]["id"]
    second_shipping_method_id = shop_data["shipping_methods"][1]["id"]
    channel_id = shop_data["channels"][0]["id"]
    warehouse_id = shop_data["warehouses"][0]["id"]

    price = 2
    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        price,
    )

    # Step 1 - Create draft order and add lines
    draft_order_input = {
        "channelId": channel_id,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        draft_order_input,
    )
    order_id = data["order"]["id"]
    assert order_id is not None

    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_lines = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_product_variant_id = order_lines["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id == product_variant_id

    # Step 2 - Update order's shipping method
    input_data = {
        "shippingMethod": first_shipping_method_id,
        "shippingAddress": DEFAULT_ADDRESS,
        "billingAddress": DEFAULT_ADDRESS,
    }
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input_data,
    )
    order_shipping_id = draft_order["order"]["deliveryMethod"]["id"]
    assert order_shipping_id == first_shipping_method_id

    # Step 3 - Update order's shipping address for country PL
    polish_address = {
        "firstName": "Jan",
        "lastName": "Kowalski",
        "phone": "+48123456787",
        "companyName": "Saleor PL",
        "country": "PL",
        "countryArea": "",
        "city": "WROCLAW",
        "postalCode": "53-346",
        "streetAddress1": "Smolna",
        "streetAddress2": "13/1",
    }
    update_input = {"shippingAddress": polish_address}
    draft_update = draft_order_update(
        e2e_staff_api_client,
        order_id,
        update_input,
    )
    draft_order_shipping_id = draft_update["order"]["deliveryMethod"]["id"]
    assert draft_order_shipping_id == order_shipping_id

    # Step 4 - Complete the order and check that 2nd shipping method is now available
    order_complete = raw_draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )

    assert (
        order_complete["errors"][0]["message"]
        == "Shipping method is not valid for chosen shipping address"
    )
    order_details = order_query(
        e2e_staff_api_client,
        order_id,
    )
    order_shipping_method = order_details["availableShippingMethods"][0]["id"]
    assert order_shipping_method == second_shipping_method_id
