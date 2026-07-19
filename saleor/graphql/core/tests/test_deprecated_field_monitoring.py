from unittest.mock import patch

import graphene
import pytest

from ....shipping.utils import convert_to_shipping_method_data
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...tests.utils import get_graphql_content
from ...webhook.subscription_payload import (
    generate_payload_from_subscription,
    generate_payload_promise_from_subscription,
)
from ...webhook.tests.test_subscription_payload import initialize_request

# These tests use `Order.token` as a representative deprecated field to verify field usage monitoring.
# If `Order.token` is ever removed from the schema, replace it with another deprecated field.

QUERY_WITH_DEPRECATED_FIELD = """
    query GetOrder($id: ID!) {
        order(id: $id) {
            token
        }
    }
"""

QUERY_WITH_DEPRECATED_FIELD_ALIASED = """
    query GetOrder($id: ID!) {
        order(id: $id) {
            orderToken: token
        }
    }
"""

QUERY_WITH_DEPRECATED_FIELD_IN_FRAGMENT = """
    fragment OrderFields on Order {
        token
    }

    query GetOrder($id: ID!) {
        order(id: $id) {
            ...OrderFields
        }
    }
"""

QUERY_WITHOUT_DEPRECATED_FIELD = """
    query GetOrder($id: ID!) {
        order(id: $id) {
            number
        }
    }
"""

SUBSCRIPTION_QUERY_WITH_DEPRECATED_FIELD = """
    subscription {
        event {
            ... on OrderUpdated {
                order {
                    token
                }
            }
        }
    }
"""

# `ShippingListMethodsForCheckout.shippingMethods` is declared with
# `monitor_usage=True` (not deprecated) and is used here to test the explicit
# opt-in monitoring path. If the field is ever removed or its `monitor_usage`
# flag is dropped, replace with another field that carries `monitor_usage=True`.
SUBSCRIPTION_QUERY_WITH_MONITORED_FIELD = """
    subscription {
        event {
            ... on ShippingListMethodsForCheckout {
                shippingMethods {
                    id
                    name
                }
            }
        }
    }
"""

SUBSCRIPTION_QUERY_WITHOUT_DEPRECATED_FIELD = """
    subscription {
        event {
            ... on OrderUpdated {
                order {
                    number
                }
            }
        }
    }
"""


# `DraftOrderCreate.orderErrors` is a deprecated field and is used here to
# test that deprecated field usage is monitored in mutations.
# If the field is ever removed from the schema, replace it with another deprecated
# mutation output field.
MUTATION_WITH_DEPRECATED_FIELD = """
    mutation CreateDraftOrder($input: DraftOrderCreateInput!) {
        draftOrderCreate(input: $input) {
            orderErrors {
                field
                message
            }
        }
    }
"""

MUTATION_WITHOUT_DEPRECATED_FIELD = """
    mutation CreateDraftOrder($input: DraftOrderCreateInput!) {
        draftOrderCreate(input: $input) {
            errors {
                field
                message
            }
        }
    }
"""


@pytest.mark.parametrize(
    "query",
    [
        QUERY_WITH_DEPRECATED_FIELD,
        QUERY_WITH_DEPRECATED_FIELD_ALIASED,
        QUERY_WITH_DEPRECATED_FIELD_IN_FRAGMENT,
    ],
    ids=["direct", "alias", "fragment"],
)
@patch("saleor.graphql.api.record_field_usage")
def test_deprecated_field_query_triggers_monitoring(
    mock_record, query, staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    get_graphql_content(response)

    # then
    mock_record.assert_called_once_with("Order", "token", True)


@patch("saleor.graphql.api.record_field_usage")
def test_non_deprecated_field_query_does_not_trigger_monitoring(
    mock_record, staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(QUERY_WITHOUT_DEPRECATED_FIELD, variables)
    get_graphql_content(response)

    # then
    mock_record.assert_not_called()


@patch("saleor.graphql.api.record_field_usage")
def test_deprecated_field_mutation_triggers_monitoring(
    mock_record, staff_api_client, permission_group_manage_orders, channel_USD
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"input": {"channelId": channel_id}}

    # when
    response = staff_api_client.post_graphql(MUTATION_WITH_DEPRECATED_FIELD, variables)
    get_graphql_content(response)

    # then
    mock_record.assert_called_once_with("DraftOrderCreate", "orderErrors", True)


@patch("saleor.graphql.api.record_field_usage")
def test_non_deprecated_field_mutation_does_not_trigger_monitoring(
    mock_record, staff_api_client, permission_group_manage_orders, channel_USD
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"input": {"channelId": channel_id}}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_WITHOUT_DEPRECATED_FIELD, variables
    )
    get_graphql_content(response)

    # then
    mock_record.assert_not_called()


@patch("saleor.graphql.api.record_field_usage")
def test_deprecated_field_subscription_payload_triggers_monitoring(
    mock_record, order, subscription_webhook, app
):
    # given
    webhook = subscription_webhook(
        SUBSCRIPTION_QUERY_WITH_DEPRECATED_FIELD,
        WebhookEventAsyncType.ORDER_UPDATED,
    )
    request = initialize_request(app=webhook.app)

    # when
    generate_payload_from_subscription(
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
        subscribable_object=order,
        subscription_query=webhook.subscription_query,
        request=request,
    )

    # then
    mock_record.assert_called_once_with("Order", "token", True)


@patch("saleor.graphql.api.record_field_usage")
def test_deprecated_field_subscription_promise_payload_triggers_monitoring(
    mock_record, order, subscription_webhook
):
    # given
    webhook = subscription_webhook(
        SUBSCRIPTION_QUERY_WITH_DEPRECATED_FIELD,
        WebhookEventAsyncType.ORDER_UPDATED,
    )
    request = initialize_request(app=webhook.app)

    # when
    promise = generate_payload_promise_from_subscription(
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
        subscribable_object=order,
        subscription_query=webhook.subscription_query,
        request=request,
    )
    promise.get()

    # then
    mock_record.assert_called_once_with("Order", "token", True)


@patch("saleor.graphql.api.record_field_usage")
def test_non_deprecated_field_subscription_payload_does_not_trigger_monitoring(
    mock_record, order, subscription_webhook, app
):
    # given
    webhook = subscription_webhook(
        SUBSCRIPTION_QUERY_WITHOUT_DEPRECATED_FIELD,
        WebhookEventAsyncType.ORDER_UPDATED,
    )
    request = initialize_request(app=webhook.app)

    # when
    generate_payload_from_subscription(
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
        subscribable_object=order,
        subscription_query=webhook.subscription_query,
        request=request,
    )

    # then
    mock_record.assert_not_called()


@patch("saleor.graphql.api.record_field_usage")
def test_monitor_usage_field_subscription_payload_triggers_monitoring(
    mock_record,
    checkout_with_shipping_required,
    shipping_method,
    address,
    subscription_webhook,
):
    # given
    checkout = checkout_with_shipping_required
    checkout.shipping_address = address
    webhook = subscription_webhook(
        SUBSCRIPTION_QUERY_WITH_MONITORED_FIELD,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )
    request = initialize_request(app=webhook.app)
    shipping_method_data = convert_to_shipping_method_data(
        shipping_method,
        shipping_method.channel_listings.get(channel=checkout.channel),
    )

    # when
    generate_payload_from_subscription(
        event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        subscribable_object=(checkout, [shipping_method_data]),
        subscription_query=webhook.subscription_query,
        request=request,
    )

    # then
    mock_record.assert_called_once_with(
        "ShippingListMethodsForCheckout", "shippingMethods", False
    )
