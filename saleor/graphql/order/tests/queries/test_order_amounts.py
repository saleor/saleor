from decimal import Decimal

import pytest

from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

ORDERS_QUERY_WITH_AMOUNT_FIELDS = """
query OrdersQuery {
    orders(first: 1) {
        edges {
            node {
                totalAuthorized{
                    amount
                    currency
                }
                totalCanceled{
                    amount
                    currency
                }
                totalCharged{
                    amount
                    currency
                }
                totalCaptured{
                    amount
                    currency
                }
                totalBalance{
                    amount
                    currency
                }
                shippingPrice {
                    gross {
                        amount
                    }
                }
                totalRefunded{
                    currency
                    amount
                }
                totalRemainingGrant{
                    currency
                    amount
                }
                totalGrantedRefund{
                    currency
                    amount
                }
                totalRefundPending{
                    currency
                    amount
                }
                totalAuthorizePending{
                    currency
                    amount
                }
                totalChargePending{
                    currency
                    amount
                }
                totalCancelPending{
                    currency
                    amount
                }
                transactions{
                    pspReference
                    modifiedAt
                    createdAt
                    authorizedAmount{
                        amount
                        currency
                    }
                    chargedAmount{
                        currency
                        amount
                    }
                    refundedAmount{
                        currency
                        amount
                    }
                    canceledAmount{
                        currency
                        amount
                    }
                    events{
                        pspReference
                        message
                        createdAt
                    }
                }
                subtotal {
                    net {
                        amount
                    }
                }
                total {
                    net {
                        amount
                    }
                }
            }
        }
    }
}
 """


def test_order_total_refunded_query_with_transactions_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_refund_amount = Decimal("10.00")
    second_refund_amount = Decimal("12.50")
    order.payment_transactions.create(
        refunded_value=first_refund_amount,
        currency=order.currency,
    )
    order.payment_transactions.create(
        refunded_value=second_refund_amount,
        currency=order.currency,
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_granted_refund = order_data["totalRefunded"]
    assert total_granted_refund["amount"] == first_refund_amount + second_refund_amount


def test_order_total_refunded_query_by_user(
    user_api_client,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_refund_amount = Decimal("10.00")
    second_refund_amount = Decimal("12.50")
    order.payment_transactions.create(
        refunded_value=first_refund_amount,
        currency=order.currency,
    )
    order.payment_transactions.create(
        refunded_value=second_refund_amount,
        currency=order.currency,
    )
    query = """
    query Order($id: ID!) {
    order(id: $id) {
            totalRefunded {
                currency
                amount
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(
        query, variables={"id": to_global_id_or_none(order)}
    )

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    total_granted_refund = order_data["totalRefunded"]
    assert total_granted_refund["amount"] == first_refund_amount + second_refund_amount


def test_order_total_refunded_query_with_transactions_by_app(
    app_api_client,
    permission_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_refund_amount = Decimal("10.00")
    second_refund_amount = Decimal("12.50")
    order.payment_transactions.create(
        refunded_value=first_refund_amount,
        currency=order.currency,
    )
    order.payment_transactions.create(
        refunded_value=second_refund_amount,
        currency=order.currency,
    )

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_granted_refund = order_data["totalRefunded"]
    assert total_granted_refund["amount"] == first_refund_amount + second_refund_amount


def test_order_total_refunded_query_with_payment_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_txn_refunded,
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()
    first_refund_amount = Decimal("5.00")
    second_refund_amount = Decimal("12.50")
    refund_transaction = payment.transactions.first()
    refund_transaction.amount = first_refund_amount
    refund_transaction.save()
    refund_transaction.pk = None
    refund_transaction.amount = second_refund_amount
    refund_transaction.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_refunded = order_data["totalRefunded"]
    assert total_refunded["amount"] == first_refund_amount + second_refund_amount


def test_order_total_refunded_query_with_payment_by_app(
    app_api_client, permission_manage_orders, order_with_lines, payment_txn_refunded
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()
    first_refund_amount = Decimal("5.00")
    second_refund_amount = Decimal("12.50")
    refund_transaction = payment.transactions.first()
    refund_transaction.amount = first_refund_amount
    refund_transaction.save()
    refund_transaction.pk = None
    refund_transaction.amount = second_refund_amount
    refund_transaction.save()

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_refunded = order_data["totalRefunded"]
    assert total_refunded["amount"] == first_refund_amount + second_refund_amount


def test_order_total_refund_pending_query_with_transactions_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_pending_refund_amount = Decimal("10.00")
    second_pending_refund_amount = Decimal("12.50")
    order.payment_transactions.create(
        refund_pending_value=first_pending_refund_amount,
        currency="USD",
    )
    order.payment_transactions.create(
        refund_pending_value=second_pending_refund_amount, currency="USD"
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalRefundPending"]
    assert (
        total_pending["amount"]
        == first_pending_refund_amount + second_pending_refund_amount
    )


def test_order_total_refund_pending_query_by_user(
    user_api_client,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    query = """
    query Order($id: ID!) {
    order(id: $id) {
            totalRefundPending {
                currency
                amount
            }
        }
    }
    """
    # when
    response = user_api_client.post_graphql(
        query, variables={"id": to_global_id_or_none(order)}
    )
    # then
    assert_no_permission(response)


def test_order_total_refund_pending_query_with_transactions_by_app(
    app_api_client,
    permission_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_pending_refund_amount = Decimal("10.00")
    second_pending_refund_amount = Decimal("12.50")
    order.payment_transactions.create(
        refund_pending_value=first_pending_refund_amount,
        currency="USD",
    )
    order.payment_transactions.create(
        refund_pending_value=second_pending_refund_amount, currency="USD"
    )

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalRefundPending"]
    assert (
        total_pending["amount"]
        == first_pending_refund_amount + second_pending_refund_amount
    )


def test_order_total_refund_pending_query_with_payment_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_txn_refunded,
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalRefundPending"]
    assert total_pending["amount"] == Decimal(0)


def test_order_total_refund_pending_query_with_payment_by_app(
    app_api_client, permission_manage_orders, order_with_lines, payment_txn_refunded
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()

    app_api_client.app.permissions.add(permission_manage_orders)

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalRefundPending"]
    assert total_pending["amount"] == Decimal(0)


def test_order_total_authorize_pending_query_with_transactions_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_pending_authorize_amount = Decimal("10.00")
    second_pending_authorize_amount = Decimal("12.50")
    order.payment_transactions.create(
        authorize_pending_value=first_pending_authorize_amount,
        currency="USD",
    )
    order.payment_transactions.create(
        authorize_pending_value=second_pending_authorize_amount, currency="USD"
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalAuthorizePending"]
    assert (
        total_pending["amount"]
        == first_pending_authorize_amount + second_pending_authorize_amount
    )


def test_order_total_authorize_pending_query_by_user(
    user_api_client,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    query = """
    query Order($id: ID!) {
    order(id: $id) {
            totalAuthorizePending {
                currency
                amount
            }
        }
    }
    """
    # when
    response = user_api_client.post_graphql(
        query, variables={"id": to_global_id_or_none(order)}
    )
    # then
    assert_no_permission(response)


def test_order_total_authorize_pending_query_with_transactions_by_app(
    app_api_client,
    permission_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_pending_authorize_amount = Decimal("10.00")
    second_pending_authorize_amount = Decimal("12.50")
    order.payment_transactions.create(
        authorize_pending_value=first_pending_authorize_amount,
        currency="USD",
    )
    order.payment_transactions.create(
        authorize_pending_value=second_pending_authorize_amount, currency="USD"
    )

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalAuthorizePending"]
    assert (
        total_pending["amount"]
        == first_pending_authorize_amount + second_pending_authorize_amount
    )


def test_order_total_authorize_pending_query_with_payment_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_txn_refunded,
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalAuthorizePending"]
    assert total_pending["amount"] == Decimal(0)


def test_order_total_authorize_pending_query_with_payment_by_app(
    app_api_client, permission_manage_orders, order_with_lines, payment_txn_refunded
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()

    app_api_client.app.permissions.add(permission_manage_orders)

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalAuthorizePending"]
    assert total_pending["amount"] == Decimal(0)


def test_order_total_charge_pending_query_with_transactions_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_pending_charge_amount = Decimal("10.00")
    second_pending_charge_amount = Decimal("12.50")
    order.payment_transactions.create(
        charge_pending_value=first_pending_charge_amount,
        currency="USD",
    )
    order.payment_transactions.create(
        charge_pending_value=second_pending_charge_amount, currency="USD"
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalChargePending"]
    assert (
        total_pending["amount"]
        == first_pending_charge_amount + second_pending_charge_amount
    )


def test_order_total_charge_pending_query_by_user(
    user_api_client,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    query = """
    query Order($id: ID!) {
    order(id: $id) {
            totalChargePending {
                currency
                amount
            }
        }
    }
    """
    # when
    response = user_api_client.post_graphql(
        query, variables={"id": to_global_id_or_none(order)}
    )
    # then
    assert_no_permission(response)


def test_order_total_charge_pending_query_with_transactions_by_app(
    app_api_client,
    permission_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_pending_charge_amount = Decimal("10.00")
    second_pending_charge_amount = Decimal("12.50")
    order.payment_transactions.create(
        charge_pending_value=first_pending_charge_amount,
        currency="USD",
    )
    order.payment_transactions.create(
        charge_pending_value=second_pending_charge_amount, currency="USD"
    )

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalChargePending"]
    assert (
        total_pending["amount"]
        == first_pending_charge_amount + second_pending_charge_amount
    )


def test_order_total_charge_pending_query_with_payment_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_txn_refunded,
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalChargePending"]
    assert total_pending["amount"] == Decimal(0)


def test_order_total_charge_pending_query_with_payment_by_app(
    app_api_client, permission_manage_orders, order_with_lines, payment_txn_refunded
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()

    app_api_client.app.permissions.add(permission_manage_orders)

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalChargePending"]
    assert total_pending["amount"] == Decimal(0)


def test_order_total_cancel_pending_query_with_transactions_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_pending_cancel_amount = Decimal("10.00")
    second_pending_cancel_amount = Decimal("12.50")
    order.payment_transactions.create(
        cancel_pending_value=first_pending_cancel_amount,
        currency="USD",
    )
    order.payment_transactions.create(
        cancel_pending_value=second_pending_cancel_amount, currency="USD"
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalCancelPending"]
    assert (
        total_pending["amount"]
        == first_pending_cancel_amount + second_pending_cancel_amount
    )


def test_order_total_cancel_pending_query_by_user(
    user_api_client,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    query = """
    query Order($id: ID!) {
    order(id: $id) {
            totalCancelPending {
                currency
                amount
            }
        }
    }
    """
    # when
    response = user_api_client.post_graphql(
        query, variables={"id": to_global_id_or_none(order)}
    )
    # then
    assert_no_permission(response)


def test_order_total_cancel_pending_query_with_transactions_by_app(
    app_api_client,
    permission_manage_orders,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    first_pending_cancel_amount = Decimal("10.00")
    second_pending_cancel_amount = Decimal("12.50")
    order.payment_transactions.create(
        cancel_pending_value=first_pending_cancel_amount,
        currency="USD",
    )
    order.payment_transactions.create(
        cancel_pending_value=second_pending_cancel_amount, currency="USD"
    )

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalCancelPending"]
    assert (
        total_pending["amount"]
        == first_pending_cancel_amount + second_pending_cancel_amount
    )


def test_order_total_cancel_pending_query_with_payment_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_txn_refunded,
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalCancelPending"]
    assert total_pending["amount"] == Decimal(0)


def test_order_total_cancel_pending_query_with_payment_by_app(
    app_api_client, permission_manage_orders, order_with_lines, payment_txn_refunded
):
    # given
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()

    app_api_client.app.permissions.add(permission_manage_orders)

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_pending = order_data["totalCancelPending"]
    assert total_pending["amount"] == Decimal(0)


def test_order_total_remaining_grant_query_with_transactions_by_staff_user(
    staff_api_client, permission_group_manage_orders, fulfilled_order, staff_user
):
    # given
    order = fulfilled_order
    granted_refund_amount = Decimal("20.00")
    pending_refund_amount = Decimal("10.00")
    refund_amount = Decimal("12.50")
    order.granted_refunds.create(
        amount_value=granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    order.payment_transactions.create(
        refund_pending_value=pending_refund_amount,
        currency="USD",
    )
    order.payment_transactions.create(refunded_value=refund_amount, currency="USD")

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_remaining_grant = order_data["totalRemainingGrant"]
    assert total_remaining_grant["amount"] == max(
        granted_refund_amount - (pending_refund_amount + refund_amount), 0
    )


def test_order_total_remaining_grant_query_by_user(
    user_api_client,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    query = """
    query Order($id: ID!) {
    order(id: $id) {
            totalRemainingGrant {
                currency
                amount
            }
        }
    }
    """
    # when
    response = user_api_client.post_graphql(
        query, variables={"id": to_global_id_or_none(order)}
    )
    # then
    assert_no_permission(response)


def test_order_total_remaining_grant_query_with_transactions_by_app(
    app_api_client, permission_manage_orders, fulfilled_order, staff_user
):
    # given
    order = fulfilled_order
    granted_refund_amount = Decimal("20.00")
    pending_refund_amount = Decimal("10.00")
    refund_amount = Decimal("12.50")
    order.granted_refunds.create(
        amount_value=granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    order.payment_transactions.create(
        refund_pending_value=pending_refund_amount,
        currency="USD",
    )
    order.payment_transactions.create(refunded_value=refund_amount, currency="USD")

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_remaining_grant = order_data["totalRemainingGrant"]
    assert total_remaining_grant["amount"] == max(
        granted_refund_amount - (pending_refund_amount + refund_amount), 0
    )


def test_order_total_remaining_grant_query_with_payment_by_staff_user(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_txn_refunded,
    staff_user,
):
    # given
    granted_refund_amount = Decimal("20.00")
    order_with_lines.granted_refunds.create(
        amount_value=granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()
    first_refund_amount = Decimal("5.00")
    second_refund_amount = Decimal("12.50")
    refund_transaction = payment.transactions.first()
    refund_transaction.amount = first_refund_amount
    refund_transaction.save()
    refund_transaction.pk = None
    refund_transaction.amount = second_refund_amount
    refund_transaction.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_remaining_grant = order_data["totalRemainingGrant"]
    assert total_remaining_grant["amount"] == granted_refund_amount - (
        first_refund_amount + second_refund_amount
    )


def test_order_total_remaining_grant_query_with_payment_by_app(
    app_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_txn_refunded,
    staff_user,
):
    # given
    granted_refund_amount = Decimal("20.00")
    order_with_lines.granted_refunds.create(
        amount_value=granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    payment = payment_txn_refunded
    payment.is_active = True
    payment.save()
    first_refund_amount = Decimal("5.00")
    second_refund_amount = Decimal("12.50")
    refund_transaction = payment.transactions.first()
    refund_transaction.amount = first_refund_amount
    refund_transaction.save()
    refund_transaction.pk = None
    refund_transaction.amount = second_refund_amount
    refund_transaction.save()

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_remaining_grant = order_data["totalRemainingGrant"]
    assert total_remaining_grant["amount"] == granted_refund_amount - (
        first_refund_amount + second_refund_amount
    )


@pytest.mark.parametrize(
    (
        "amount_charged",
        "amount_authorized",
        "amount_refunded",
        "amount_canceled",
        "amount_charge_pending",
        "amount_authorize_pending",
        "amount_refund_pending",
        "amount_cancel_pending",
        "remaining_grant_amount",
    ),
    [
        ("60", "0", "0", "0", "0", "0", "0", "0", 150),
        ("0", "60", "0", "0", "0", "0", "0", "0", 150),
        ("0", "0", "60", "0", "0", "0", "0", "0", 150),
        ("0", "0", "0", "60", "0", "0", "0", "0", 150),
        ("0", "0", "0", "0", "60", "0", "0", "0", 150),
        ("0", "0", "0", "0", "0", "60", "0", "0", 150),
        ("0", "0", "0", "0", "0", "0", "60", "0", 150),
        ("0", "0", "0", "0", "0", "0", "0", "60", 150),
        ("0", "20", "0", "40", "0", "0", "0", "0", 150),
        ("45", "0", "15", "0", "0", "0", "0", "0", 150),
        ("-60", "0", "0", "0", "0", "0", "60", "0", 90),
        ("-60", "0", "60", "0", "0", "0", "0", "0", 90),
        ("-60", "60", "60", "0", "0", "0", "0", "0", 150),
    ],
)
def test_order_total_remaining_grant_query_with_transactions_total_charged(
    amount_charged,
    amount_authorized,
    amount_refunded,
    amount_canceled,
    amount_charge_pending,
    amount_authorize_pending,
    amount_refund_pending,
    amount_cancel_pending,
    remaining_grant_amount,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    staff_user,
):
    # given
    order = fulfilled_order
    order_total = Decimal("200.00")
    order.total_gross_amount = order_total
    order.total_net_amount = order_total
    order.save(update_fields=["total_gross_amount", "total_net_amount"])

    granted_refund_amount = Decimal("150.00")
    order.granted_refunds.create(
        amount_value=granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    order.payment_transactions.create(
        charged_value=Decimal(amount_charged),
        authorized_value=Decimal(amount_authorized),
        refunded_value=Decimal(amount_refunded),
        canceled_value=Decimal(amount_canceled),
        charge_pending_value=Decimal(amount_charge_pending),
        authorize_pending_value=Decimal(amount_authorize_pending),
        refund_pending_value=Decimal(amount_refund_pending),
        cancel_pending_value=Decimal(amount_cancel_pending),
        currency="USD",
    )
    order.payment_transactions.create(charged_value=order_total, currency="USD")
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_remaining_grant = order_data["totalRemainingGrant"]
    assert total_remaining_grant["amount"] == remaining_grant_amount


@pytest.mark.parametrize(
    (
        "amount_charged",
        "amount_authorized",
        "amount_refunded",
        "amount_canceled",
        "amount_charge_pending",
        "amount_authorize_pending",
        "amount_refund_pending",
        "amount_cancel_pending",
        "remaining_grant_amount",
    ),
    [
        ("60", "0", "0", "0", "0", "0", "0", "0", 10),
        ("0", "60", "0", "0", "0", "0", "0", "0", 10),
        ("0", "0", "60", "0", "0", "0", "0", "0", 0),
        ("0", "0", "0", "60", "0", "0", "0", "0", 0),
        ("0", "0", "0", "0", "60", "0", "0", "0", 10),
        ("0", "0", "0", "0", "0", "60", "0", "0", 10),
        ("0", "0", "0", "0", "0", "0", "60", "0", 0),
        ("0", "0", "0", "0", "0", "0", "0", "60", 0),
        ("0", "20", "0", "40", "0", "0", "0", "0", 0),
        ("0", "80", "0", "40", "0", "0", "0", "0", 30),
        ("45", "0", "15", "0", "0", "0", "0", "0", 0),
        ("-60", "0", "0", "0", "0", "0", "60", "0", 0),
        ("-60", "0", "60", "0", "0", "0", "0", "0", 0),
        ("-60", "60", "60", "0", "0", "0", "0", "0", 0),
    ],
)
def test_order_total_remaining_grant_query_with_transactions_total_refunded(
    amount_charged,
    amount_authorized,
    amount_refunded,
    amount_canceled,
    amount_charge_pending,
    amount_authorize_pending,
    amount_refund_pending,
    amount_cancel_pending,
    remaining_grant_amount,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    staff_user,
):
    # given
    order = fulfilled_order
    order_total = Decimal("200.00")
    order.total_gross_amount = order_total
    order.total_net_amount = order_total
    order.save(update_fields=["total_gross_amount", "total_net_amount"])

    granted_refund_amount = Decimal("150.00")
    order.granted_refunds.create(
        amount_value=granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    order.payment_transactions.create(
        charged_value=Decimal(amount_charged),
        authorized_value=Decimal(amount_authorized),
        refunded_value=Decimal(amount_refunded),
        canceled_value=Decimal(amount_canceled),
        charge_pending_value=Decimal(amount_charge_pending),
        authorize_pending_value=Decimal(amount_authorize_pending),
        refund_pending_value=Decimal(amount_refund_pending),
        cancel_pending_value=Decimal(amount_cancel_pending),
        currency="USD",
    )
    order.payment_transactions.create(refunded_value=order_total, currency="USD")
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_remaining_grant = order_data["totalRemainingGrant"]
    assert total_remaining_grant["amount"] == remaining_grant_amount


@pytest.mark.parametrize(
    (
        "amount_charged",
        "amount_authorized",
        "amount_refunded",
        "amount_canceled",
        "amount_charge_pending",
        "amount_authorize_pending",
        "amount_refund_pending",
        "amount_cancel_pending",
        "remaining_grant_amount",
    ),
    [
        ("60", "0", "0", "0", "0", "0", "0", "0", 85),
        ("0", "60", "0", "0", "0", "0", "0", "0", 85),
        ("0", "0", "60", "0", "0", "0", "0", "0", 25),
        ("0", "0", "0", "60", "0", "0", "0", "0", 25),
        ("0", "0", "0", "0", "60", "0", "0", "0", 85),
        ("0", "0", "0", "0", "0", "60", "0", "0", 85),
        ("0", "0", "0", "0", "0", "0", "60", "0", 25),
        ("0", "0", "0", "0", "0", "0", "0", "60", 25),
        ("0", "20", "0", "40", "0", "0", "0", "0", 45),
        ("0", "80", "0", "40", "0", "0", "0", "0", 105),
        ("45", "0", "15", "0", "0", "0", "0", "0", 70),
        ("-60", "0", "0", "0", "0", "0", "60", "0", 0),
        ("-60", "0", "60", "0", "0", "0", "0", "0", 0),
        ("-60", "60", "60", "0", "0", "0", "0", "0", 25),
    ],
)
def test_order_total_remaining_grant_query_with_transactions_partially_refunded(
    amount_charged,
    amount_authorized,
    amount_refunded,
    amount_canceled,
    amount_charge_pending,
    amount_authorize_pending,
    amount_refund_pending,
    amount_cancel_pending,
    remaining_grant_amount,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    staff_user,
):
    # given
    order = fulfilled_order
    order_total = Decimal("200.00")
    order.total_gross_amount = order_total
    order.total_net_amount = order_total
    order.save(update_fields=["total_gross_amount", "total_net_amount"])

    granted_refund_amount = Decimal("150.00")
    order.granted_refunds.create(
        amount_value=granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    order.payment_transactions.create(
        charged_value=Decimal(amount_charged),
        authorized_value=Decimal(amount_authorized),
        refunded_value=Decimal(amount_refunded),
        canceled_value=Decimal(amount_canceled),
        charge_pending_value=Decimal(amount_charge_pending),
        authorize_pending_value=Decimal(amount_authorize_pending),
        refund_pending_value=Decimal(amount_refund_pending),
        cancel_pending_value=Decimal(amount_cancel_pending),
        currency="USD",
    )
    order.payment_transactions.create(
        refund_pending_value=Decimal("125"), charged_value=Decimal("75"), currency="USD"
    )
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_AMOUNT_FIELDS)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_remaining_grant = order_data["totalRemainingGrant"]
    assert total_remaining_grant["amount"] == remaining_grant_amount
