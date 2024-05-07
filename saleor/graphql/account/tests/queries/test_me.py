from unittest import mock

import graphene

from .....order.models import FulfillmentStatus
from .....payment.interface import (
    ListStoredPaymentMethodsRequestData,
    PaymentGateway,
    PaymentMethodCreditCardInfo,
    PaymentMethodData,
)
from ....payment.enums import TokenizedPaymentFlowEnum
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


QUERY_ME_WITH_STORED_PAYMENT_METHODS = """
query Me($channel: String!) {
  me{
    storedPaymentMethods(channel: $channel){
      id
      gateway{
        name
        id
        config{
          field
          value
        }
        currencies
      }
      paymentMethodId
      creditCardInfo{
        brand
        firstDigits
        lastDigits
        expMonth
        expYear
      }
      supportedPaymentFlows
      type
      name
      data
    }
  }
}
"""


@mock.patch("saleor.plugins.manager.PluginsManager.list_stored_payment_methods")
def test_me_query_stored_payment_methods(
    mocked_list_stored_payment_methods, user_api_client, channel_USD, customer_user
):
    # given
    payment_method_id = "app:payment-method-id"
    external_id = "payment-method-id"
    supported_payment_flow = TokenizedPaymentFlowEnum.INTERACTIVE
    payment_method_type = "credit-card"
    payment_method_name = "Payment method name"
    payment_method_data = {"additional_data": "value"}

    payment_gateway_id = "gateway-id"
    payment_gateway_name = "gateway-name"

    credit_card_brand = "brand"
    credit_card_first_digits = "123"
    credit_card_last_digits = "456"
    credit_card_exp_month = 1
    credit_card_exp_year = 2021

    mocked_list_stored_payment_methods.return_value = [
        PaymentMethodData(
            id=payment_method_id,
            external_id=external_id,
            supported_payment_flows=[supported_payment_flow.value],
            type=payment_method_type,
            credit_card_info=PaymentMethodCreditCardInfo(
                brand=credit_card_brand,
                first_digits=credit_card_first_digits,
                last_digits=credit_card_last_digits,
                exp_month=credit_card_exp_month,
                exp_year=credit_card_exp_year,
            ),
            name=payment_method_name,
            data=payment_method_data,
            gateway=PaymentGateway(
                id=payment_gateway_id,
                name=payment_gateway_name,
                currencies=[channel_USD.currency_code],
                config=[],
            ),
        )
    ]

    request_data = ListStoredPaymentMethodsRequestData(
        user=user_api_client.user,
        channel=channel_USD,
    )

    query = QUERY_ME_WITH_STORED_PAYMENT_METHODS

    # when
    response = user_api_client.post_graphql(
        query,
        variables={
            "channel": channel_USD.slug,
        },
    )

    # then
    mocked_list_stored_payment_methods.assert_called_once_with(request_data)
    content = get_graphql_content(response)

    data = content["data"]["me"]
    assert data["storedPaymentMethods"] == [
        {
            "id": payment_method_id,
            "gateway": {
                "name": payment_gateway_name,
                "id": payment_gateway_id,
                "config": [],
                "currencies": [channel_USD.currency_code],
            },
            "paymentMethodId": external_id,
            "creditCardInfo": {
                "brand": credit_card_brand,
                "firstDigits": credit_card_first_digits,
                "lastDigits": credit_card_last_digits,
                "expMonth": credit_card_exp_month,
                "expYear": credit_card_exp_year,
            },
            "supportedPaymentFlows": [supported_payment_flow.name],
            "type": payment_method_type,
            "name": payment_method_name,
            "data": payment_method_data,
        }
    ]
