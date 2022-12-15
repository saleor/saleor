import pytest
from graphene import Node

from .....order import OrderStatus
from ....tests.utils import get_graphql_content

DRAFT_ORDER_UPDATE_MUTATION = """
mutation draftUpdate(
  $id: ID!
  $voucher: ID!
  $customerNote: String
  $shippingAddress: AddressInput
  $billingAddress: AddressInput
) {
  draftOrderUpdate(
    id: $id
    input: {
      voucher: $voucher
      customerNote: $customerNote
      shippingAddress: $shippingAddress
      billingAddress: $billingAddress
    }
  ) {
    errors {
      field
      message
    }
  }
}
"""


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.save(update_fields=["status"])
    return order_with_lines


def test_draft_order_update_shipping_address_invalidate_prices(
    staff_api_client,
    permission_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
):
    # given
    query = DRAFT_ORDER_UPDATE_MUTATION
    variables = {
        "id": Node.to_global_id("Order", draft_order.id),
        "voucher": Node.to_global_id("Voucher", voucher.id),
        "shippingAddress": graphql_address_data,
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_orders]
        )
    )

    # then
    assert not content["data"]["draftOrderUpdate"]["errors"]
    draft_order.refresh_from_db()
    assert draft_order.should_refresh_prices


def test_draft_order_update_billing_address_invalidate_prices(
    staff_api_client,
    permission_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
):
    # given
    query = DRAFT_ORDER_UPDATE_MUTATION
    variables = {
        "id": Node.to_global_id("Order", draft_order.id),
        "voucher": Node.to_global_id("Voucher", voucher.id),
        "billingAddress": graphql_address_data,
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_orders]
        )
    )

    # then
    assert not content["data"]["draftOrderUpdate"]["errors"]
    draft_order.refresh_from_db()
    assert draft_order.should_refresh_prices


ORDER_UPDATE_MUTATION = """
mutation orderUpdate(
  $id: ID!
  $email: String
  $shippingAddress: AddressInput
  $billingAddress: AddressInput
) {
  orderUpdate(
    id: $id
    input: {
      userEmail: $email
      shippingAddress: $shippingAddress
      billingAddress: $billingAddress
    }
  ) {
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


def test_order_update_shipping_address_invalidate_prices(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    order = order_with_lines
    order.user = None
    order.save()
    query = ORDER_UPDATE_MUTATION
    variables = {
        "id": Node.to_global_id("Order", order.id),
        "shippingAddress": graphql_address_data,
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_orders]
        )
    )

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    order.refresh_from_db()
    assert order.should_refresh_prices


def test_order_update_billing_address_invalidate_prices(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    order = order_with_lines
    order.user = None
    order.save()
    query = ORDER_UPDATE_MUTATION
    variables = {
        "id": Node.to_global_id("Order", order.id),
        "billingAddress": graphql_address_data,
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_orders]
        )
    )

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    order.refresh_from_db()
    assert order.should_refresh_prices


ORDER_LINES_CREATE_MUTATION = """
mutation OrderLinesCreate(
  $orderId: ID!
  $variantId: ID!
  $quantity: Int!
) {
  orderLinesCreate(
    id: $orderId
    input: [
      {
        variantId: $variantId
        quantity: $quantity
      }
    ]
  ) {
    errors {
      field
      message
    }
  }
}
"""


def test_order_lines_create_invalidate_prices(
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    variant = line.variant
    variables = {
        "orderId": Node.to_global_id("Order", order.id),
        "variantId": Node.to_global_id("ProductVariant", variant.id),
        "quantity": 2,
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_orders]
        )
    )

    # then
    assert not content["data"]["orderLinesCreate"]["errors"]
    order.refresh_from_db()
    assert order.should_refresh_prices


ORDER_LINE_UPDATE_MUTATION = """
mutation OrderLineUpdate(
  $lineId: ID!
  $quantity: Int!
) {
  orderLineUpdate(
    id: $lineId
    input: {
      quantity: $quantity
    }
  ) {
    errors {
        field
        message
    }
  }
}
"""


def test_order_line_update_invalidate_prices(
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    staff_user,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    variables = {"lineId": Node.to_global_id("OrderLine", line.id), "quantity": 1}

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_orders]
        )
    )

    # then
    assert not content["data"]["orderLineUpdate"]["errors"]
    order.refresh_from_db()
    assert order.should_refresh_prices


ORDER_LINE_DELETE_MUTATION = """
mutation OrderLineDelete(
  $id: ID!
) {
  orderLineDelete(
    id: $id
  ) {
    errors {
      field
      message
    }
  }
}
"""


def test_order_line_remove(
    order_with_lines, permission_manage_orders, staff_api_client
):
    # given
    order = order_with_lines
    line = order.lines.first()
    query = ORDER_LINE_DELETE_MUTATION
    variables = {"id": Node.to_global_id("OrderLine", line.id)}

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_orders]
        )
    )

    # then
    assert not content["data"]["orderLineDelete"]["errors"]
    order.refresh_from_db()
    assert order.should_refresh_prices
