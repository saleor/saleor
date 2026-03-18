from unittest.mock import patch

import pytest

from .....site import PasswordLoginMode
from ...account.utils.token_create import raw_token_create
from ...conftest import E2eApiClient
from ...product.utils.category import create_category
from ...product.utils.product import PRODUCT_CREATE_MUTATION
from ...product.utils.product_type import create_product_type
from ...utils import assign_permissions, get_graphql_content

ORDERS_QUERY = """
query Orders {
    orders(first: 10) {
        edges {
            node {
                id
            }
        }
    }
}
"""


@pytest.mark.e2e
@patch("saleor.account.throttling.cache")
def test_staff_token_has_no_permissions_in_customers_only_mode(
    _mocked_cache,
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    site_settings,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_product_types_and_attributes,
):
    # Step 1: Assign permissions and prepare product type and category
    assign_permissions(
        e2e_staff_api_client,
        [
            permission_manage_orders,
            permission_manage_products,
            permission_manage_product_types_and_attributes,
        ],
    )
    product_type = create_product_type(e2e_staff_api_client)
    category = create_category(e2e_staff_api_client)

    staff_email = e2e_staff_api_client.user.email
    staff_password = "password"
    product_input = {
        "input": {
            "name": "Test product",
            "productType": product_type["id"],
            "category": category["id"],
        }
    }

    # Step 2: Login with ENABLED mode and create a product, fetch orders — should succeed
    login_response = raw_token_create(
        e2e_not_logged_api_client, staff_email, staff_password
    )
    login_data = login_response["data"]["tokenCreate"]
    assert login_data["errors"] == []
    enabled_token = login_data["token"]

    enabled_client = E2eApiClient()
    enabled_client.token = enabled_token

    response = enabled_client.post_graphql(PRODUCT_CREATE_MUTATION, product_input)
    content = get_graphql_content(response)
    assert content["data"]["productCreate"]["errors"] == []
    assert content["data"]["productCreate"]["product"]["id"] is not None

    response = enabled_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)
    assert content["data"]["orders"] is not None

    # Step 3: Switch to CUSTOMERS_ONLY mode
    site_settings.password_login_mode = PasswordLoginMode.CUSTOMERS_ONLY
    site_settings.save(update_fields=["password_login_mode"])

    # Step 4: Try to create a product and fetch orders — should fail
    response = enabled_client.post_graphql(PRODUCT_CREATE_MUTATION, product_input)
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"

    response = enabled_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"

    # Step 5: Switch back to ENABLED mode — should succeed again
    site_settings.password_login_mode = PasswordLoginMode.ENABLED
    site_settings.save(update_fields=["password_login_mode"])

    response = enabled_client.post_graphql(PRODUCT_CREATE_MUTATION, product_input)
    content = get_graphql_content(response)
    assert content["data"]["productCreate"]["errors"] == []
    assert content["data"]["productCreate"]["product"]["id"] is not None

    response = enabled_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)
    assert content["data"]["orders"] is not None
