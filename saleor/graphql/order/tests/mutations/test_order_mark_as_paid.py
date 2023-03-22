import graphene
from prices import Money, TaxedMoney

from .....order import OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_MARK_ORDER_AS_PAID = """
    mutation markPaid($id: ID!, $transaction: String) {
        orderMarkAsPaid(id: $id, transactionReference: $transaction) {
            errors {
                field
                message
            }
            errors {
                field
                message
                code
            }
            order {
                isPaid
                events{
                    transactionReference
                }
            }
        }
    }
"""


def test_paid_order_mark_as_paid(
    staff_api_client, permission_group_manage_orders, payment_txn_preauth
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = payment_txn_preauth.order
    query = MUTATION_MARK_ORDER_AS_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    errors = content["data"]["orderMarkAsPaid"]["errors"]
    msg = "Orders with payments can not be manually marked as paid."
    assert errors[0]["message"] == msg
    assert errors[0]["field"] == "payment"

    order_errors = content["data"]["orderMarkAsPaid"]["errors"]
    assert order_errors[0]["code"] == OrderErrorCode.PAYMENT_ERROR.name


def test_order_mark_as_paid_with_external_reference(
    staff_api_client, permission_group_manage_orders, order_with_lines, staff_user
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    transaction_reference = "searchable-id"
    order = order_with_lines
    query = MUTATION_MARK_ORDER_AS_PAID
    assert not order.is_fully_paid()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "transaction": transaction_reference}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    data = content["data"]["orderMarkAsPaid"]["order"]
    order.refresh_from_db()
    assert data["isPaid"] is True
    assert len(data["events"]) == 1
    assert data["events"][0]["transactionReference"] == transaction_reference
    assert order.is_fully_paid()
    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_MARKED_AS_PAID
    assert event_order_paid.user == staff_user
    event_reference = event_order_paid.parameters.get("transaction_reference")
    assert event_reference == transaction_reference
    order_payments = order.payments.filter(psp_reference=transaction_reference)
    assert order_payments.count() == 1


def test_order_mark_as_paid(
    staff_api_client, permission_group_manage_orders, order_with_lines, staff_user
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    query = MUTATION_MARK_ORDER_AS_PAID
    assert not order.is_fully_paid()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderMarkAsPaid"]["order"]
    order.refresh_from_db()
    assert data["isPaid"] is True is order.is_fully_paid()

    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_MARKED_AS_PAID
    assert event_order_paid.user == staff_user


def test_paid_order_mark_as_paid_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    order_with_lines,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    query = MUTATION_MARK_ORDER_AS_PAID

    assert not order.is_fully_paid()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    query = MUTATION_MARK_ORDER_AS_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_order_mark_as_paid_by_app(
    app_api_client, permission_manage_orders, order_with_lines
):
    # given
    order = order_with_lines
    query = MUTATION_MARK_ORDER_AS_PAID
    assert not order.is_fully_paid()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderMarkAsPaid"]["order"]
    order.refresh_from_db()
    assert data["isPaid"] is True is order.is_fully_paid()

    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_MARKED_AS_PAID
    assert event_order_paid.user is None
    assert event_order_paid.app == app_api_client.app


def test_order_mark_as_paid_no_billing_address(
    staff_api_client, permission_group_manage_orders, order_with_lines, staff_user
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_with_lines.billing_address = None
    order_with_lines.save()

    query = MUTATION_MARK_ORDER_AS_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderMarkAsPaid"]["errors"]
    assert data[0]["code"] == OrderErrorCode.BILLING_ADDRESS_NOT_SET.name


def test_draft_order_mark_as_paid_check_price_recalculation(
    staff_api_client, permission_group_manage_orders, order_with_lines, staff_user
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    # we need to change order total and set it as invalidated prices.
    # we couldn't use `order.total.gross` because this test don't use any tax app
    # or plugin.
    expected_total_net = order.total.net
    expected_total = TaxedMoney(net=expected_total_net, gross=expected_total_net)
    order.total = TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))
    order.should_refresh_prices = True
    order.status = OrderStatus.DRAFT
    order.save()
    query = MUTATION_MARK_ORDER_AS_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderMarkAsPaid"]["order"]
    order.refresh_from_db()
    assert order.total == expected_total
    payment = order.payments.get()
    assert payment.total == expected_total_net.amount
    assert data["isPaid"] is True is order.is_fully_paid()
    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_MARKED_AS_PAID
    assert event_order_paid.user == staff_user
