from decimal import Decimal
from unittest import mock

import graphene
import pytest

from .....order import OrderStatus
from .....payment import TransactionEventType
from .....payment.interface import TransactionSessionResult
from ....account.tests.mutations.permission_group.test_permission_group_update import (
    PERMISSION_GROUP_UPDATE_MUTATION,
)
from ....order.enums import OrderChargeStatusEnum
from ....tests.utils import assert_no_permission, get_graphql_content
from ..mutations.test_draft_order_complete import DRAFT_ORDER_COMPLETE_MUTATION
from ..mutations.test_draft_order_create import DRAFT_ORDER_CREATE_MUTATION
from ..mutations.test_draft_order_update import DRAFT_ORDER_UPDATE_MUTATION
from ..mutations.test_order_lines_create import ORDER_LINES_CREATE_MUTATION
from ..mutations.test_order_mark_as_paid import MARK_ORDER_AS_PAID_MUTATION
from ..queries.test_order import QUERY_ORDER_BY_ID


@pytest.mark.integration
def test_create_order_by_staff_in_accessible_channel(
    staff_api_client,
    permission_group_manage_orders,
    channel_PLN,
    channel_USD,
    product,
    shipping_method,
    graphql_address_data,
):
    # given
    permission_group_manage_orders.restricted_access_to_channels = True
    permission_group_manage_orders.save(update_fields=["restricted_access_to_channels"])
    permission_group_manage_orders.channels.add(channel_USD)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when

    # create order
    draft_order_create_variables = {
        "input": {
            "userEmail": "test@example.com",
            "billingAddress": graphql_address_data,
            "shippingAddress": graphql_address_data,
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
        }
    }
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_CREATE_MUTATION, draft_order_create_variables
    )

    draft_order_id = get_graphql_content(response)["data"]["draftOrderCreate"]["order"][
        "id"
    ]

    # add lines to order
    variant = product.variants.first()
    order_lines_create_variables = {
        "orderId": draft_order_id,
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.id),
        "quantity": 2,
    }
    staff_api_client.post_graphql(
        ORDER_LINES_CREATE_MUTATION, order_lines_create_variables
    )

    # update order with available product and shipping method
    draft_order_update_variables = {
        "id": draft_order_id,
        "input": {
            "shippingMethod": graphene.Node.to_global_id(
                "ShippingMethod", shipping_method.id
            ),
        },
    }
    staff_api_client.post_graphql(
        DRAFT_ORDER_UPDATE_MUTATION, draft_order_update_variables
    )

    # complete order
    staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, {"id": draft_order_id})

    # then
    # query created order
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, {"id": draft_order_id})
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()


@pytest.mark.integration
def test_user_cannot_manage_draft_order_after_losing_access_to_channel(
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
    graphql_address_data,
    product,
    shipping_method,
    superuser_api_client,
):
    # given
    permission_group_manage_orders.restricted_access_to_channels = True
    permission_group_manage_orders.save(update_fields=["restricted_access_to_channels"])
    permission_group_manage_orders.channels.add(channel_USD)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variant = product.variants.first()

    # when

    # create draft order
    draft_order_create_variables = {
        "input": {
            "userEmail": "test@example.com",
            "billingAddress": graphql_address_data,
            "shippingAddress": graphql_address_data,
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "lines": [
                {
                    "quantity": 1,
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                }
            ],
            "shippingMethod": graphene.Node.to_global_id(
                "ShippingMethod", shipping_method.id
            ),
        }
    }
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_CREATE_MUTATION, draft_order_create_variables
    )

    draft_order_id = get_graphql_content(response)["data"]["draftOrderCreate"]["order"][
        "id"
    ]

    # complete order
    staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, {"id": draft_order_id})

    # update permission group - remove access to order channel
    permission_group_update_variables = {
        "id": graphene.Node.to_global_id("Group", permission_group_manage_orders.id),
        "input": {
            "restrictedAccessToChannels": True,
            "removeChannels": [graphene.Node.to_global_id("Channel", channel_USD.id)],
        },
    }
    superuser_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, permission_group_update_variables
    )

    # try to mark order as paid
    response = staff_api_client.post_graphql(
        MARK_ORDER_AS_PAID_MUTATION, {"id": draft_order_id}
    )

    # then
    assert_no_permission(response)


DRAFT_ORDER_CREATE = """
mutation draftOrderCreate($input: DraftOrderCreateInput!) {
  draftOrderCreate(input: $input) {
    errors { field code message }
    order { id }
  }
}
"""

ORDER_LINES_CREATE = """
mutation orderLinesCreate($id: ID!, $input: [OrderLineCreateInput!]!) {
  orderLinesCreate(id: $id, input: $input) {
    errors { field code message }
    orderLines { id }
  }
}
"""

ORDER_LINE_DELETE = """
mutation orderLineDelete($id: ID!) {
  orderLineDelete(id: $id) {
    errors { field code message }
  }
}
"""

DRAFT_ORDER_UPDATE_ADDRESSES = """
mutation draftOrderUpdate($id: ID!, $input: DraftOrderInput!) {
  draftOrderUpdate(id: $id, input: $input) {
    errors { field code message }
  }
}
"""

ORDER_UPDATE_SHIPPING = """
mutation orderUpdateShipping($order: ID!, $input: OrderUpdateShippingInput!) {
  orderUpdateShipping(order: $order, input: $input) {
    errors { field code message }
  }
}
"""

TRANSACTION_INITIALIZE = """
mutation transactionInitialize(
  $id: ID!, $amount: PositiveDecimal!, $paymentGateway: PaymentGatewayToInitialize!
) {
  transactionInitialize(id: $id, amount: $amount, paymentGateway: $paymentGateway) {
    errors { field code message }
    transaction { id chargedAmount { amount } }
  }
}
"""

ORDER_TOTAL_QUERY = """
query order($id: ID!) {
  order(id: $id) {
    total { gross { amount } }
  }
}
"""

ORDER_CHARGE_STATUS_QUERY = """
query order($id: ID!) {
  order(id: $id) {
    chargeStatus
  }
}
"""

DRAFT_ORDER_COMPLETE = """
mutation draftOrderComplete($id: ID!) {
  draftOrderComplete(id: $id) {
    errors { field code message }
    order { id chargeStatus total { gross { amount } } }
  }
}
"""


def _create_order_line(api_client, order_id, variant_id, quantity):
    response = api_client.post_graphql(
        ORDER_LINES_CREATE,
        {
            "id": order_id,
            "input": [{"variantId": variant_id, "quantity": quantity}],
        },
    )
    data = get_graphql_content(response)["data"]["orderLinesCreate"]
    assert data["errors"] == []
    return data["orderLines"][0]["id"]


def _set_shipping_method(api_client, order_id, shipping_method):
    response = api_client.post_graphql(
        ORDER_UPDATE_SHIPPING,
        {
            "order": order_id,
            "input": {
                "shippingMethod": graphene.Node.to_global_id(
                    "ShippingMethod", shipping_method.pk
                )
            },
        },
    )
    assert get_graphql_content(response)["data"]["orderUpdateShipping"]["errors"] == []


def _fetch_total(api_client, order_id):
    """Read the order total, which also persists the recalculated prices."""
    response = api_client.post_graphql(ORDER_TOTAL_QUERY, {"id": order_id})
    order_data = get_graphql_content(response)["data"]["order"]
    return Decimal(str(order_data["total"]["gross"]["amount"]))


def _fetch_charge_status(api_client, order_id):
    response = api_client.post_graphql(ORDER_CHARGE_STATUS_QUERY, {"id": order_id})
    return get_graphql_content(response)["data"]["order"]["chargeStatus"]


@pytest.mark.integration
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_draft_order_charge_status_when_total_changes_after_the_order_is_charged(
    mocked_initialize,
    staff_api_client,
    user_api_client,
    permission_group_manage_orders,
    channel_USD,
    product,
    shipping_method,
    graphql_address_data,
    webhook_app,
    transaction_session_response,
):
    """Charge status calculated against a stale draft total is refreshed on complete.

    A draft order is charged for the total the customer was shown, while the order
    total stored in the database is lower, as the lines have been changed in the
    meantime. The charge status calculated at that point is `OVERCHARGED`, and the
    completion recalculation, which brings the total back to the charged amount, has
    to refresh it.
    """
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variant_id = graphene.Node.to_global_id(
        "ProductVariant", product.variants.first().pk
    )
    app_identifier = "webhook.app.identifier"
    webhook_app.identifier = app_identifier
    webhook_app.save(update_fields=["identifier"])

    # when
    # create an empty draft order
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_CREATE,
        {
            "input": {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "userEmail": "customer@example.com",
            }
        },
    )
    data = get_graphql_content(response)["data"]["draftOrderCreate"]
    assert data["errors"] == []
    order_id = data["order"]["id"]

    # add the lines, the addresses and the shipping method
    line_id = _create_order_line(staff_api_client, order_id, variant_id, quantity=2)
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_UPDATE_ADDRESSES,
        {
            "id": order_id,
            "input": {
                "shippingAddress": graphql_address_data,
                "billingAddress": graphql_address_data,
            },
        },
    )
    assert get_graphql_content(response)["data"]["draftOrderUpdate"]["errors"] == []
    _set_shipping_method(staff_api_client, order_id, shipping_method)

    # the total the customer is charged for
    amount_to_charge = _fetch_total(staff_api_client, order_id)

    # drop the line, so that the stored total no longer covers the charged amount
    response = staff_api_client.post_graphql(ORDER_LINE_DELETE, {"id": line_id})
    assert get_graphql_content(response)["data"]["orderLineDelete"]["errors"] == []
    assert _fetch_total(staff_api_client, order_id) < amount_to_charge

    # charge the order for the amount the customer was shown
    gateway_response = transaction_session_response.copy()
    gateway_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    gateway_response["amount"] = str(amount_to_charge)
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=app_identifier, response=gateway_response
    )
    response = user_api_client.post_graphql(
        TRANSACTION_INITIALIZE,
        {
            "id": order_id,
            "amount": amount_to_charge,
            "paymentGateway": {"id": app_identifier, "data": None},
        },
    )
    transaction_data = get_graphql_content(response)["data"]["transactionInitialize"]
    assert transaction_data["errors"] == []
    assert (
        Decimal(str(transaction_data["transaction"]["chargedAmount"]["amount"]))
        == amount_to_charge
    )

    assert (
        _fetch_charge_status(staff_api_client, order_id)
        == OrderChargeStatusEnum.OVERCHARGED.name
    )

    # bring the line and the shipping method back, so that the order total matches
    # the charged amount again
    _create_order_line(staff_api_client, order_id, variant_id, quantity=2)
    _set_shipping_method(staff_api_client, order_id, shipping_method)

    # then
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE, {"id": order_id})
    data = get_graphql_content(response)["data"]["draftOrderComplete"]
    assert data["errors"] == []
    assert Decimal(str(data["order"]["total"]["gross"]["amount"])) == amount_to_charge
    assert data["order"]["chargeStatus"] == OrderChargeStatusEnum.FULL.name
