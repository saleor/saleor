from unittest.mock import patch

import graphene

from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from .....product.models import ProductVariant
from ....tests.utils import get_graphql_content

ORDER_UPDATE_MUTATION = """
    mutation orderUpdate($id: ID!, $email: String, $address: AddressInput) {
        orderUpdate(
            id: $id, input: {
                userEmail: $email,
                shippingAddress: $address,
                billingAddress: $address}) {
            errors {
                field
                code
            }
            order {
                userEmail
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "email": email, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        ORDER_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    order_updated_webhook_mock.assert_called_once_with(order)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_with_draft_order(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    draft_order,
    graphql_address_data,
):
    order = draft_order
    order.user = None
    order.save()
    email = "not_default@example.com"
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "email": email, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        ORDER_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["orderUpdate"]["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == OrderErrorCode.INVALID.name
    order_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_without_sku(
    plugin_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    ProductVariant.objects.update(sku=None)
    order_with_lines.lines.update(product_sku=None)

    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "email": email, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        ORDER_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    assert plugin_mock.called is True


def test_order_update_anonymous_user_no_user_email(
    staff_api_client, order_with_lines, permission_manage_orders, graphql_address_data
):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
            mutation orderUpdate(
            $id: ID!, $address: AddressInput) {
                orderUpdate(
                    id: $id, input: {
                        shippingAddress: $address,
                        billingAddress: $address}) {
                    errors {
                        field
                        message
                    }
                    order {
                        id
                    }
                }
            }
            """
    first_name = "Test fname"
    last_name = "Test lname"
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)
    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name != first_name
    assert order.billing_address.last_name != last_name
    assert order.status == OrderStatus.UNFULFILLED


def test_order_update_user_email_existing_user(
    staff_api_client,
    order_with_lines,
    customer_user,
    permission_manage_orders,
    graphql_address_data,
):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
        mutation orderUpdate(
        $id: ID!, $email: String, $address: AddressInput) {
            orderUpdate(
                id: $id, input: {
                    userEmail: $email, shippingAddress: $address,
                    billingAddress: $address}) {
                errors {
                    field
                    message
                }
                order {
                    userEmail
                }
            }
        }
        """
    email = customer_user.email
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "address": graphql_address_data, "email": email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user == customer_user
