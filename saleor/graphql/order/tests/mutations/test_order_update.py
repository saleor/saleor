from unittest.mock import patch

import graphene

from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from .....product.models import ProductVariant
from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_UPDATE_MUTATION = """
    mutation orderUpdate(
        $id: ID!, $email: String, $address: AddressInput, $externalReference: String
    ) {
        orderUpdate(
            id: $id,
            input: {
                userEmail: $email,
                externalReference: $externalReference,
                shippingAddress: $address,
                billingAddress: $address
                }
            ) {
            errors {
                field
                code
            }
            order {
                userEmail
                externalReference
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    external_reference = "test-ext-ref"

    variables = {
        "id": order_id,
        "email": email,
        "address": graphql_address_data,
        "externalReference": external_reference,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email
    assert data["externalReference"] == external_reference

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.shipping_address.validation_skipped is False
    assert order.billing_address.validation_skipped is False
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    assert order.external_reference == external_reference
    order_updated_webhook_mock.assert_called_once_with(order)


def test_order_update_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    order_with_lines,
    graphql_address_data,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = order_with_lines

    order.user = None
    order.channel = channel_PLN
    order.save(update_fields=["channel", "user"])

    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    external_reference = "test-ext-ref"

    variables = {
        "id": order_id,
        "email": email,
        "address": graphql_address_data,
        "externalReference": external_reference,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_by_app(
    order_updated_webhook_mock,
    app_api_client,
    permission_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    external_reference = "test-ext-ref"

    variables = {
        "id": order_id,
        "email": email,
        "address": graphql_address_data,
        "externalReference": external_reference,
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_UPDATE_MUTATION, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email
    assert data["externalReference"] == external_reference

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    assert order.external_reference == external_reference
    order_updated_webhook_mock.assert_called_once_with(order)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_with_draft_order(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    graphql_address_data,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.user = None
    order.save()
    email = "not_default@example.com"
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "email": email, "address": graphql_address_data}
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    error = content["data"]["orderUpdate"]["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == OrderErrorCode.INVALID.name
    order_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_without_sku(
    plugin_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
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
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    graphql_address_data,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    response = staff_api_client.post_graphql(query, variables)
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
    permission_group_manage_orders,
    graphql_address_data,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    response = staff_api_client.post_graphql(query, variables)
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


ORDER_UPDATE_BY_EXTERNAL_REFERENCE = """
    mutation orderUpdate(
        $id: ID
        $externalReference: String
        $input: OrderUpdateInput!
    ) {
        orderUpdate(
            id: $id
            externalReference: $externalReference
            input: $input
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
                externalReference
                shippingAddress {
                    firstName
                }
            }
        }
    }
    """


def test_order_update_by_external_reference(
    staff_api_client, permission_group_manage_orders, order, graphql_address_data
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    ext_ref = "test-ext-ref"
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])

    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    variables = {
        "externalReference": ext_ref,
        "input": {"shippingAddress": graphql_address_data},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdate"]
    assert not data["errors"]
    assert data["order"]["externalReference"] == ext_ref
    assert data["order"]["id"] == graphene.Node.to_global_id("Order", order.id)
    assert (
        data["order"]["shippingAddress"]["firstName"]
        == graphql_address_data["firstName"]
    )
    order.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]


def test_order_update_by_both_id_and_external_reference(
    staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    variables = {
        "id": "test-id",
        "externalReference": "test-ext-ref",
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdate"]
    assert not data["order"]
    assert (
        data["errors"][0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_order_update_by_external_reference_not_existing(
    staff_api_client, permission_group_manage_orders, voucher_free_shipping
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {
        "externalReference": ext_ref,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdate"]
    assert not data["order"]
    assert data["errors"][0]["message"] == f"Couldn't resolve to a node: {ext_ref}"


def test_order_update_with_non_unique_external_reference(
    staff_api_client, permission_group_manage_orders, order, order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    ext_ref = "test-ext-ref"
    order_1 = order_list[0]
    order_1.external_reference = ext_ref
    order_1.save(update_fields=["external_reference"])
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id, "input": {"externalReference": ext_ref}}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["orderUpdate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == OrderErrorCode.UNIQUE.name
    assert error["message"] == "Order with this External reference already exists."


ORDER_UPDATE_MUTATION_WITH_ADDRESS = """
    mutation orderUpdate($id: ID!, $address: AddressInput) {
        orderUpdate(
            id: $id,
            input: {
                shippingAddress: $address,
                billingAddress: $address
                }
            ) {
            errors {
                field
                code
            }
            order {
                shippingAddress {
                    postalCode
                }
                billingAddress {
                    postalCode
                }
            }
        }
    }
"""


def test_order_update_invalid_address_skip_validation(
    staff_api_client,
    permission_group_manage_orders,
    order,
    graphql_address_data_skipped_validation,
):
    # given
    address_data = graphql_address_data_skipped_validation
    invalid_postal_code = "invalid_postal_code"
    address_data["postalCode"] = invalid_postal_code
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_MUTATION_WITH_ADDRESS
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdate"]
    assert not data["errors"]
    assert data["order"]["shippingAddress"]["postalCode"] == invalid_postal_code
    assert data["order"]["billingAddress"]["postalCode"] == invalid_postal_code
    order.refresh_from_db()
    assert order.shipping_address.postal_code == invalid_postal_code
    assert order.shipping_address.validation_skipped is True
    assert order.billing_address.postal_code == invalid_postal_code
    assert order.billing_address.validation_skipped is True
