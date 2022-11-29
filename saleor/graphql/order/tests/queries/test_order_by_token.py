import graphene

from .....core.anonymize import obfuscate_email
from .....order.models import Order
from ....tests.utils import assert_no_permission, get_graphql_content
from ..utils import assert_order_and_payment_ids

ORDER_BY_TOKEN_QUERY = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            id
            shippingAddress {
                firstName
                lastName
                streetAddress1
                streetAddress2
                phone
            }
            billingAddress {
                firstName
                lastName
                streetAddress1
                streetAddress2
                phone
            }
            userEmail
        }
    }
    """


def test_order_by_token_query_by_anonymous_user(api_client, order):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.billing_address.street_address_2 = "test"
    order.billing_address.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_order_owner(user_api_client, order):
    # given
    query = ORDER_BY_TOKEN_QUERY
    order.user = user_api_client.user
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = user_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_old_id_query_by_anonymous_user(api_client, order):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    order.billing_address.street_address_2 = "test"
    order.billing_address.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id
    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name[
        0
    ] + "." * (len(order.shipping_address.first_name) - 1)
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name[
        0
    ] + "." * (len(order.shipping_address.last_name) - 1)
    assert data["shippingAddress"][
        "streetAddress1"
    ] == order.shipping_address.street_address_1[0] + "." * (
        len(order.shipping_address.street_address_1) - 1
    )
    assert data["shippingAddress"][
        "streetAddress2"
    ] == order.shipping_address.street_address_2[0] + "." * (
        len(order.shipping_address.street_address_2) - 1
    )
    assert data["shippingAddress"]["phone"] == str(order.shipping_address.phone)[
        :3
    ] + "." * (len(str(order.shipping_address.phone)) - 3)

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name[
        0
    ] + "." * (len(order.billing_address.first_name) - 1)
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name[
        0
    ] + "." * (len(order.billing_address.last_name) - 1)
    assert data["billingAddress"][
        "streetAddress1"
    ] == order.billing_address.street_address_1[0] + "." * (
        len(order.billing_address.street_address_1) - 1
    )
    assert data["billingAddress"][
        "streetAddress2"
    ] == order.billing_address.street_address_2[0] + "." * (
        len(order.billing_address.street_address_2) - 1
    )
    assert data["billingAddress"]["phone"] == str(order.billing_address.phone)[
        :3
    ] + "." * (len(str(order.billing_address.phone)) - 3)
    assert data["userEmail"] == obfuscate_email(order.user_email)


def test_order_by_token_query_by_superuser(superuser_api_client, order):
    # given
    query = ORDER_BY_TOKEN_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = superuser_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_staff_with_permission(
    staff_api_client, permission_manage_orders, order, customer_user
):
    # given
    query = ORDER_BY_TOKEN_QUERY

    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_orders)

    order.user = customer_user
    order.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_staff_no_permission(
    staff_api_client, order, customer_user
):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.shipping_address.street_address_2 = "test"
    order.shipping_address.save()

    order.user = customer_user
    order.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.user = customer_user
    order.save()

    app_api_client.app.permissions.add(permission_manage_orders)

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = app_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_token_query_by_app_no_perm(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order.user = customer_user
    order.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = app_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == order_id

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name
    assert (
        data["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert (
        data["shippingAddress"]["streetAddress2"]
        == order.shipping_address.street_address_2
    )
    assert data["shippingAddress"]["phone"] == order.shipping_address.phone

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name
    assert (
        data["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        data["billingAddress"]["streetAddress2"]
        == order.billing_address.street_address_2
    )
    assert data["billingAddress"]["phone"] == order.billing_address.phone

    assert data["userEmail"] == order.user_email


def test_order_by_old_id_query_by_app_no_perm(app_api_client, order, customer_user):
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    query = ORDER_BY_TOKEN_QUERY

    order.user = customer_user
    order.save()

    # when
    response = app_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["id"] == graphene.Node.to_global_id("Order", order.id)

    assert data["shippingAddress"]["firstName"] == order.shipping_address.first_name[
        0
    ] + "." * (len(order.shipping_address.first_name) - 1)
    assert data["shippingAddress"]["lastName"] == order.shipping_address.last_name[
        0
    ] + "." * (len(order.shipping_address.last_name) - 1)
    assert data["shippingAddress"][
        "streetAddress1"
    ] == order.shipping_address.street_address_1[0] + "." * (
        len(order.shipping_address.street_address_1) - 1
    )
    assert data["shippingAddress"]["streetAddress2"] == ""
    assert data["shippingAddress"]["phone"] == str(order.shipping_address.phone)[
        :3
    ] + "." * (len(str(order.shipping_address.phone)) - 3)

    assert data["billingAddress"]["firstName"] == order.billing_address.first_name[
        0
    ] + "." * (len(order.billing_address.first_name) - 1)
    assert data["billingAddress"]["lastName"] == order.billing_address.last_name[
        0
    ] + "." * (len(order.billing_address.last_name) - 1)
    assert data["billingAddress"][
        "streetAddress1"
    ] == order.billing_address.street_address_1[0] + "." * (
        len(order.billing_address.street_address_1) - 1
    )
    assert data["billingAddress"]["streetAddress2"] == ""
    assert data["billingAddress"]["phone"] == str(order.billing_address.phone)[
        :3
    ] + "." * (len(str(order.billing_address.phone)) - 3)


def test_query_draft_order_by_token_with_requester_as_customer(
    user_api_client, draft_order
):
    draft_order.user = user_api_client.user
    draft_order.save(update_fields=["user"])
    query = ORDER_BY_TOKEN_QUERY
    response = user_api_client.post_graphql(query, {"token": draft_order.id})
    content = get_graphql_content(response)
    assert not content["data"]["orderByToken"]


def test_query_draft_order_by_token_as_anonymous_customer(api_client, draft_order):
    query = ORDER_BY_TOKEN_QUERY
    response = api_client.post_graphql(query, {"token": draft_order.id})
    content = get_graphql_content(response)
    assert not content["data"]["orderByToken"]


def test_query_order_without_addresses(order, user_api_client, channel_USD):
    # given
    query = ORDER_BY_TOKEN_QUERY

    order = Order.objects.create(
        channel=channel_USD,
        user=user_api_client.user,
    )

    # when
    response = user_api_client.post_graphql(query, {"token": order.id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["userEmail"] == user_api_client.user.email
    assert data["billingAddress"] is None
    assert data["shippingAddress"] is None


def test_order_query_address_without_order_user(
    staff_api_client, permission_manage_orders, channel_USD, address
):
    query = ORDER_BY_TOKEN_QUERY
    shipping_address = address.get_copy()
    billing_address = address.get_copy()
    order = Order.objects.create(
        channel=channel_USD,
        shipping_address=shipping_address,
        billing_address=billing_address,
    )
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, {"token": order.id})
    content = get_graphql_content(response)
    order = content["data"]["orderByToken"]
    assert order["shippingAddress"] is not None
    assert order["billingAddress"] is not None


def test_order_by_token_user_restriction(api_client, order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            user {
                id
            }
        }
    }
    """
    response = api_client.post_graphql(query, {"token": order.id})
    assert_no_permission(response)


def test_order_by_token_events_restriction(api_client, order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            events {
                id
            }
        }
    }
    """
    response = api_client.post_graphql(query, {"token": order.id})
    assert_no_permission(response)


def test_authorized_access_to_order_by_token(
    user_api_client, staff_api_client, customer_user, order, permission_manage_users
):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            user {
                id
            }
        }
    }
    """
    variables = {"token": order.id}
    customer_user_id = graphene.Node.to_global_id("User", customer_user.id)

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["orderByToken"]["user"]["id"] == customer_user_id

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    assert content["data"]["orderByToken"]["user"]["id"] == customer_user_id


QUERY_ORDER_BY_TOKEN_WITH_PAYMENT = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token){
            id
            payments{
              id
              gateway
              isActive
              created
              modified
              paymentMethodType
              transactions{
                gatewayResponse

              }
              actions
              capturedAmount{
                amount
              }
              availableCaptureAmount{
                amount
              }
              availableRefundAmount{
                amount
              }

              creditCard{
                brand
                firstDigits
                lastDigits
                expMonth
                expYear
              }
            }
        }
  }
"""


def test_order_by_token_query_for_payment_details_without_permissions(
    api_client, payment_txn_captured
):
    response = api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_WITH_PAYMENT, {"token": payment_txn_captured.order.id}
    )
    assert_no_permission(response)


def test_order_by_token_query_for_payment_details_with_permissions(
    staff_api_client, payment_txn_captured, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_WITH_PAYMENT,
        {"token": payment_txn_captured.order.id},
    )

    content = get_graphql_content(response)

    assert_order_and_payment_ids(content, payment_txn_captured)


QUERY_ORDER_WITH_PAYMENT_AVAILABLE_FIELDS = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token){
            id
            payments{
              id
              gateway
              isActive
              created
              modified
              paymentMethodType
              capturedAmount{
                amount
              }
              chargeStatus
              creditCard{
                brand
                firstDigits
                lastDigits
                expMonth
                expYear
              }
            }
        }
  }
"""


def test_order_by_token_query_payment_details_available_fields_without_permissions(
    api_client, payment_txn_captured
):
    response = api_client.post_graphql(
        QUERY_ORDER_WITH_PAYMENT_AVAILABLE_FIELDS,
        {"token": payment_txn_captured.order.id},
    )

    content = get_graphql_content(response)

    assert_order_and_payment_ids(content, payment_txn_captured)


def test_order_by_token_query_payment_details_available_fields_with_permissions(
    staff_api_client, payment_txn_captured, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_ORDER_WITH_PAYMENT_AVAILABLE_FIELDS,
        {"token": payment_txn_captured.order.id},
    )

    content = get_graphql_content(response)

    assert_order_and_payment_ids(content, payment_txn_captured)
