import graphene

from .....order.models import FulfillmentStatus
from ....tests.utils import assert_no_permission, get_graphql_content

ME_QUERY = """
    query Me {
        me {
            id
            email
            checkout {
                token
            }
            userPermissions {
                code
                name
            }
            checkouts(first: 10) {
                edges {
                    node {
                        id
                    }
                }
                totalCount
            }
        }
    }
"""


def test_me_query(user_api_client):
    response = user_api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert data["email"] == user_api_client.user.email


def test_me_user_permissions_query(
    user_api_client, permission_manage_users, permission_group_manage_users
):
    user = user_api_client.user
    user.user_permissions.add(permission_manage_users)
    user.groups.add(permission_group_manage_users)
    response = user_api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    user_permissions = content["data"]["me"]["userPermissions"]

    assert len(user_permissions) == 1
    assert user_permissions[0]["code"] == permission_manage_users.codename.upper()


def test_me_query_anonymous_client(api_client):
    response = api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    assert content["data"]["me"] is None


def test_me_query_customer_can_not_see_note(
    staff_user, staff_api_client, permission_manage_users
):
    query = """
    query Me {
        me {
            id
            email
            note
        }
    }
    """
    # Random person (even staff) can't see own note without permissions
    response = staff_api_client.post_graphql(query)
    assert_no_permission(response)

    # Add permission and ensure staff can see own note
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert data["email"] == staff_api_client.user.email
    assert data["note"] == staff_api_client.user.note


def test_me_query_checkout(user_api_client, checkout):
    user = user_api_client.user
    checkout.user = user
    checkout.save()

    response = user_api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert data["checkout"]["token"] == str(checkout.token)
    assert data["checkouts"]["edges"][0]["node"]["id"] == graphene.Node.to_global_id(
        "Checkout", checkout.pk
    )


def test_me_query_checkout_with_inactive_channel(user_api_client, checkout):
    user = user_api_client.user
    channel = checkout.channel
    channel.is_active = False
    channel.save()
    checkout.user = user
    checkout.save()

    response = user_api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert not data["checkout"]
    assert not data["checkouts"]["edges"]


def test_me_query_checkouts_with_channel(user_api_client, checkout, checkout_JPY):
    query = """
        query Me($channel: String) {
            me {
                checkouts(first: 10, channel: $channel) {
                    edges {
                        node {
                            id
                            channel {
                                slug
                            }
                        }
                    }
                    totalCount
                }
            }
        }
    """

    user = user_api_client.user
    checkout.user = checkout_JPY.user = user
    checkout.save()
    checkout_JPY.save()

    response = user_api_client.post_graphql(query, {"channel": checkout.channel.slug})

    content = get_graphql_content(response)
    data = content["data"]["me"]["checkouts"]
    assert data["edges"][0]["node"]["id"] == graphene.Node.to_global_id(
        "Checkout", checkout.pk
    )
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["channel"]["slug"] == checkout.channel.slug


QUERY_ME_CHECKOUT_TOKENS = """
query getCheckoutTokens($channel: String) {
  me {
    checkoutTokens(channel: $channel)
  }
}
"""


def test_me_checkout_tokens_without_channel_param(
    user_api_client, checkouts_assigned_to_customer
):
    # given
    checkouts = checkouts_assigned_to_customer

    # when
    response = user_api_client.post_graphql(QUERY_ME_CHECKOUT_TOKENS)

    # then
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert len(data["checkoutTokens"]) == len(checkouts)
    for checkout in checkouts:
        assert str(checkout.token) in data["checkoutTokens"]


def test_me_checkout_tokens_without_channel_param_inactive_channel(
    user_api_client, channel_PLN, checkouts_assigned_to_customer
):
    # given
    channel_PLN.is_active = False
    channel_PLN.save()
    checkouts = checkouts_assigned_to_customer

    # when
    response = user_api_client.post_graphql(QUERY_ME_CHECKOUT_TOKENS)

    # then
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert str(checkouts[0].token) in data["checkoutTokens"]
    assert str(checkouts[1].token) not in data["checkoutTokens"]


def test_me_checkout_tokens_with_channel(
    user_api_client, channel_USD, checkouts_assigned_to_customer
):
    # given
    checkouts = checkouts_assigned_to_customer

    # when
    response = user_api_client.post_graphql(
        QUERY_ME_CHECKOUT_TOKENS, {"channel": channel_USD.slug}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert str(checkouts[0].token) in data["checkoutTokens"]
    assert str(checkouts[1].token) not in data["checkoutTokens"]


def test_me_checkout_tokens_with_inactive_channel(
    user_api_client, channel_USD, checkouts_assigned_to_customer
):
    # given
    channel_USD.is_active = False
    channel_USD.save()

    # when
    response = user_api_client.post_graphql(
        QUERY_ME_CHECKOUT_TOKENS, {"channel": channel_USD.slug}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert not data["checkoutTokens"]


def test_me_checkout_tokens_with_not_existing_channel(
    user_api_client, checkouts_assigned_to_customer
):
    # given

    # when
    response = user_api_client.post_graphql(
        QUERY_ME_CHECKOUT_TOKENS, {"channel": "Not-existing"}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert not data["checkoutTokens"]


def test_me_with_cancelled_fulfillments(
    user_api_client, fulfilled_order_with_cancelled_fulfillment
):
    query = """
    query Me {
        me {
            orders (first: 1) {
                edges {
                    node {
                        id
                        fulfillments {
                            status
                        }
                    }
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_id = graphene.Node.to_global_id(
        "Order", fulfilled_order_with_cancelled_fulfillment.id
    )
    data = content["data"]["me"]
    order = data["orders"]["edges"][0]["node"]
    assert order["id"] == order_id
    fulfillments = order["fulfillments"]
    assert len(fulfillments) == 1
    assert fulfillments[0]["status"] == FulfillmentStatus.FULFILLED.upper()
