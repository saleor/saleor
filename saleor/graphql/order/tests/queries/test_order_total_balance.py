from decimal import Decimal

from .....core.prices import quantize_price
from .....order.models import OrderGrantedRefund
from .....payment.models import TransactionItem
from ....tests.utils import get_graphql_content

ORDERS_QUERY = """
query OrdersQuery {
    orders(first: 1) {
        edges {
            node {
                totalBalance{
                    amount
                    currency
                }
            }
        }
    }
}
"""


def test_total_balance_only_charged(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    transactions = TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                charged_value=Decimal("15"),
            ),
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                charged_value=Decimal("19"),
                available_actions=[],
            ),
        ]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_charged = sum([t.charged_value for t in transactions], Decimal(0))
    total_balance = quantize_price(
        total_charged - order.total.gross.amount, order.currency
    )
    assert (
        quantize_price(Decimal(order_data["totalBalance"]["amount"]), order.currency)
        == total_balance
    )


def test_total_balance_charged_and_pending_charged(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    transactions = TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                charged_value=Decimal("15"),
            ),
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                charge_pending_value=Decimal("19"),
                available_actions=[],
            ),
        ]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_charged = sum([t.charged_value for t in transactions], Decimal(0))
    total_charged += sum([t.charge_pending_value for t in transactions], Decimal(0))
    total_balance = quantize_price(
        total_charged - order.total.gross.amount, order.currency
    )
    assert (
        quantize_price(Decimal(order_data["totalBalance"]["amount"]), order.currency)
        == total_balance
    )


def test_total_balance_only_refunded(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                refunded_value=Decimal("15"),
            ),
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                refunded_value=Decimal("19"),
                available_actions=[],
            ),
        ]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_balance = quantize_price(-order.total.gross.amount, order.currency)
    assert (
        quantize_price(Decimal(order_data["totalBalance"]["amount"]), order.currency)
        == total_balance
    )


def test_total_balance_refunded_and_pending_refund(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                refunded_value=Decimal("15"),
            ),
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                refund_pending_value=Decimal("19"),
                available_actions=[],
            ),
        ]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_balance = quantize_price(-order.total.gross.amount, order.currency)
    assert (
        quantize_price(Decimal(order_data["totalBalance"]["amount"]), order.currency)
        == total_balance
    )


def test_total_balance_refunded_and_charged(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    transactions = TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                refunded_value=Decimal("15"),
            ),
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                charged_value=Decimal("19"),
                available_actions=[],
            ),
        ]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_charged = sum([t.charged_value for t in transactions], Decimal(0))
    total_balance = quantize_price(
        total_charged - order.total.gross.amount, order.currency
    )
    assert (
        quantize_price(Decimal(order_data["totalBalance"]["amount"]), order.currency)
        == total_balance
    )


def test_total_balance_with_granted_refund(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    granted_refund = OrderGrantedRefund.objects.create(
        amount_value=Decimal("10.15"), currency=order.currency, order_id=order.pk
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_balance = quantize_price(
        -(order.total.gross.amount - granted_refund.amount_value), order.currency
    )
    assert (
        quantize_price(Decimal(order_data["totalBalance"]["amount"]), order.currency)
        == total_balance
    )


def test_total_balance_with_granted_refund_and_transactions(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    granted_refund = OrderGrantedRefund.objects.create(
        amount_value=Decimal("10.15"), currency=order.currency, order_id=order.pk
    )
    transactions = TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                refunded_value=Decimal("15"),
            ),
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                refund_pending_value=Decimal("19"),
                available_actions=[],
            ),
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                charged_value=Decimal("11"),
                available_actions=[],
            ),
            TransactionItem(
                order_id=order.id,
                name="Credit card",
                psp_reference="111",
                currency="USD",
                charge_pending_value=Decimal("12"),
                available_actions=[],
            ),
        ]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_charged = sum([t.charged_value for t in transactions], Decimal(0))
    total_charged += sum([t.charge_pending_value for t in transactions], Decimal(0))
    total_balance = quantize_price(
        total_charged - (order.total.gross.amount - granted_refund.amount_value),
        order.currency,
    )
    assert (
        quantize_price(Decimal(order_data["totalBalance"]["amount"]), order.currency)
        == total_balance
    )
