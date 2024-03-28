from decimal import Decimal

import graphene
from prices import Money, TaxedMoney

from saleor.payment import TransactionEventType

from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import OrderGrantedRefundStatusEnum

ORDERS_QUERY = """
query OrdersQuery {
    orders(first: 1) {
        edges {
            node {
                number
                totalGrantedRefund {
                    currency
                    amount
                }
                grantedRefunds{
                    id
                    createdAt
                    updatedAt
                    amount{
                        amount
                        currency
                    }
                    reason
                    user{
                        id
                    }
                    app{
                        id
                    }
                    shippingCostsIncluded
                    lines{
                        id
                        orderLine{
                          id
                        }
                        quantity
                    }
                    status
                    transactionEvents{
                      id
                    }
                    transaction{
                      id
                    }
                }
            }
        }
    }
}
"""


def test_order_granted_refunds_query_without_lines_by_user(
    staff_user,
    app,
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    net = Money(amount=Decimal("10"), currency="USD")
    gross = Money(amount=net.amount * Decimal(1.23), currency="USD").quantize()
    shipping_price = TaxedMoney(net=net, gross=gross)
    order.shipping_price = shipping_price
    shipping_tax_rate = Decimal("0.23")
    order.shipping_tax_rate = shipping_tax_rate
    order.save()
    first_granted_refund = order.granted_refunds.create(
        amount_value=Decimal("10.0"),
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    second_granted_refund = order.granted_refunds.create(
        amount_value=Decimal("12.5"), currency="USD", reason="Test reason", app=app
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    granted_refunds = order_data["grantedRefunds"]
    assert len(granted_refunds) == 2
    assert granted_refunds == [
        {
            "id": to_global_id_or_none(first_granted_refund),
            "createdAt": first_granted_refund.created_at.isoformat(),
            "updatedAt": first_granted_refund.updated_at.isoformat(),
            "amount": {
                "amount": float(first_granted_refund.amount.amount),
                "currency": first_granted_refund.currency,
            },
            "reason": first_granted_refund.reason,
            "user": {"id": to_global_id_or_none(first_granted_refund.user)},
            "app": None,
            "shippingCostsIncluded": False,
            "lines": [],
            "status": OrderGrantedRefundStatusEnum.NONE.name,
            "transactionEvents": [],
            "transaction": None,
        },
        {
            "id": to_global_id_or_none(second_granted_refund),
            "createdAt": second_granted_refund.created_at.isoformat(),
            "updatedAt": second_granted_refund.updated_at.isoformat(),
            "amount": {
                "amount": float(second_granted_refund.amount.amount),
                "currency": second_granted_refund.currency,
            },
            "reason": second_granted_refund.reason,
            "app": {"id": to_global_id_or_none(second_granted_refund.app)},
            "user": None,
            "shippingCostsIncluded": False,
            "lines": [],
            "status": OrderGrantedRefundStatusEnum.NONE.name,
            "transactionEvents": [],
            "transaction": None,
        },
    ]


def test_order_granted_refunds_query_without_lines_by_app(
    staff_user,
    app,
    app_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    permission_manage_users,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    net = Money(amount=Decimal("10"), currency="USD")
    gross = Money(amount=net.amount * Decimal(1.23), currency="USD").quantize()
    shipping_price = TaxedMoney(net=net, gross=gross)
    order.shipping_price = shipping_price
    shipping_tax_rate = Decimal("0.23")
    order.shipping_tax_rate = shipping_tax_rate
    order.save()
    first_granted_refund = order.granted_refunds.create(
        amount_value=Decimal("10.0"),
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    second_granted_refund = order.granted_refunds.create(
        amount_value=Decimal("12.5"), currency="USD", reason="Test reason", app=app
    )

    app_api_client.app.permissions.set(
        [permission_manage_orders, permission_manage_shipping, permission_manage_users]
    )

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    granted_refunds = order_data["grantedRefunds"]
    assert len(granted_refunds) == 2
    assert granted_refunds == [
        {
            "id": to_global_id_or_none(first_granted_refund),
            "createdAt": first_granted_refund.created_at.isoformat(),
            "updatedAt": first_granted_refund.updated_at.isoformat(),
            "amount": {
                "amount": float(first_granted_refund.amount.amount),
                "currency": first_granted_refund.currency,
            },
            "reason": first_granted_refund.reason,
            "user": {"id": to_global_id_or_none(first_granted_refund.user)},
            "app": None,
            "shippingCostsIncluded": False,
            "lines": [],
            "status": OrderGrantedRefundStatusEnum.NONE.name,
            "transactionEvents": [],
            "transaction": None,
        },
        {
            "id": to_global_id_or_none(second_granted_refund),
            "createdAt": second_granted_refund.created_at.isoformat(),
            "updatedAt": second_granted_refund.updated_at.isoformat(),
            "amount": {
                "amount": float(second_granted_refund.amount.amount),
                "currency": second_granted_refund.currency,
            },
            "reason": second_granted_refund.reason,
            "app": {"id": to_global_id_or_none(second_granted_refund.app)},
            "user": None,
            "shippingCostsIncluded": False,
            "lines": [],
            "status": OrderGrantedRefundStatusEnum.NONE.name,
            "transactionEvents": [],
            "transaction": None,
        },
    ]


def test_order_granted_refunds_query_by_user(
    staff_user,
    app,
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_shipping,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    net = Money(amount=Decimal("10"), currency="USD")
    gross = Money(amount=net.amount * Decimal(1.23), currency="USD").quantize()
    shipping_price = TaxedMoney(net=net, gross=gross)
    order.shipping_price = shipping_price
    shipping_tax_rate = Decimal("0.23")
    order.shipping_tax_rate = shipping_tax_rate
    order.save()
    granted_refund = order.granted_refunds.create(
        amount_value=Decimal("10.0"),
        currency="USD",
        reason="Test reason",
        user=staff_user,
        shipping_costs_included=True,
    )
    order_line = order.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    granted_refunds = order_data["grantedRefunds"]
    assert len(granted_refunds) == 1
    assert granted_refunds == [
        {
            "id": to_global_id_or_none(granted_refund),
            "createdAt": granted_refund.created_at.isoformat(),
            "updatedAt": granted_refund.updated_at.isoformat(),
            "amount": {
                "amount": float(granted_refund.amount.amount),
                "currency": granted_refund.currency,
            },
            "reason": granted_refund.reason,
            "user": {"id": to_global_id_or_none(granted_refund.user)},
            "app": None,
            "shippingCostsIncluded": True,
            "lines": [
                {
                    "id": to_global_id_or_none(granted_refund_line),
                    "quantity": granted_refund_line.quantity,
                    "orderLine": {
                        "id": to_global_id_or_none(order_line),
                    },
                }
            ],
            "status": OrderGrantedRefundStatusEnum.NONE.name,
            "transactionEvents": [],
            "transaction": None,
        },
    ]


def test_order_granted_refunds_query_by_app(
    staff_user,
    app,
    app_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    permission_manage_users,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    net = Money(amount=Decimal("10"), currency="USD")
    gross = Money(amount=net.amount * Decimal(1.23), currency="USD").quantize()
    shipping_price = TaxedMoney(net=net, gross=gross)
    order.shipping_price = shipping_price
    shipping_tax_rate = Decimal("0.23")
    order.shipping_tax_rate = shipping_tax_rate
    order.save()
    granted_refund = order.granted_refunds.create(
        amount_value=Decimal("10.0"),
        currency="USD",
        reason="Test reason",
        app=app,
        shipping_costs_included=True,
    )
    order_line = order.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)

    app_api_client.app.permissions.set(
        [permission_manage_orders, permission_manage_shipping, permission_manage_users]
    )

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    granted_refunds = order_data["grantedRefunds"]
    assert len(granted_refunds) == 1
    assert granted_refunds == [
        {
            "id": to_global_id_or_none(granted_refund),
            "createdAt": granted_refund.created_at.isoformat(),
            "updatedAt": granted_refund.updated_at.isoformat(),
            "amount": {
                "amount": float(granted_refund.amount.amount),
                "currency": granted_refund.currency,
            },
            "reason": granted_refund.reason,
            "user": None,
            "app": {"id": to_global_id_or_none(granted_refund.app)},
            "shippingCostsIncluded": True,
            "lines": [
                {
                    "id": to_global_id_or_none(granted_refund_line),
                    "quantity": granted_refund_line.quantity,
                    "orderLine": {
                        "id": to_global_id_or_none(order_line),
                    },
                }
            ],
            "status": OrderGrantedRefundStatusEnum.NONE.name,
            "transactionEvents": [],
            "transaction": None,
        },
    ]


def test_order_total_granted_refund_query_by_staff_user(
    staff_user,
    app,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    first_granted_refund_amount = Decimal("10.00")
    second_granted_refund_amount = Decimal("12.50")
    order.granted_refunds.create(
        amount_value=first_granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    order.granted_refunds.create(
        amount_value=second_granted_refund_amount,
        currency="USD",
        reason="Test reason",
        app=app,
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_granted_refund = order_data["totalGrantedRefund"]
    assert (
        total_granted_refund["amount"]
        == first_granted_refund_amount + second_granted_refund_amount
    )


def test_order_total_granted_refund_query_by_user(
    user_api_client,
    staff_user,
    app,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    first_granted_refund_amount = Decimal("10.00")
    second_granted_refund_amount = Decimal("12.50")
    order.granted_refunds.create(
        amount_value=first_granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    order.granted_refunds.create(
        amount_value=second_granted_refund_amount,
        currency="USD",
        reason="Test reason",
        app=app,
    )
    query = """
    query Order($id: ID!) {
    order(id: $id) {
            totalGrantedRefund {
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


def test_order_total_granted_refund_query_by_app(
    staff_user,
    app,
    app_api_client,
    permission_manage_orders,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    first_granted_refund_amount = Decimal("10.00")
    second_granted_refund_amount = Decimal("12.50")
    order.granted_refunds.create(
        amount_value=first_granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )
    order.granted_refunds.create(
        amount_value=second_granted_refund_amount,
        currency="USD",
        reason="Test reason",
        app=app,
    )

    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    total_granted_refund = order_data["totalGrantedRefund"]
    assert (
        total_granted_refund["amount"]
        == first_granted_refund_amount + second_granted_refund_amount
    )


def test_order_granted_refunds_query_with_removed_app(
    staff_user,
    removed_app,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    first_granted_refund_amount = Decimal("10.00")
    order.granted_refunds.create(
        amount_value=first_granted_refund_amount,
        currency="USD",
        reason="Test reason",
        app=removed_app,
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    granted_refund = order_data["grantedRefunds"][0]
    assert granted_refund["app"] is None


def test_order_granted_refund_with_assigned_transaction(
    app,
    app_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    permission_manage_users,
    fulfilled_order,
    transaction_item_generator,
):
    # given
    order = fulfilled_order
    transaction = transaction_item_generator(
        order_id=order.pk, charged_value=Decimal("10.0")
    )
    order.granted_refunds.create(
        amount_value=Decimal("10.0"),
        currency="USD",
        reason="Test reason",
        app=app,
        shipping_costs_included=True,
        transaction_item=transaction,
    )

    app_api_client.app.permissions.set(
        [permission_manage_orders, permission_manage_shipping, permission_manage_users]
    )

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    granted_refunds = order_data["grantedRefunds"]
    assert len(granted_refunds) == 1
    assert granted_refunds[0]["transaction"]["id"] == graphene.Node.to_global_id(
        "TransactionItem", transaction.token
    )


def test_order_granted_refund_with_status(
    app,
    app_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    permission_manage_users,
    fulfilled_order,
    transaction_item_generator,
):
    # given
    order = fulfilled_order
    transaction = transaction_item_generator(
        order_id=order.pk, charged_value=Decimal("10.0")
    )
    order.granted_refunds.create(
        amount_value=Decimal("10.0"),
        currency="USD",
        reason="Test reason",
        app=app,
        shipping_costs_included=True,
        transaction_item=transaction,
    )

    app_api_client.app.permissions.set(
        [permission_manage_orders, permission_manage_shipping, permission_manage_users]
    )

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    granted_refunds = order_data["grantedRefunds"]
    assert len(granted_refunds) == 1
    assert granted_refunds[0]["status"] == OrderGrantedRefundStatusEnum.NONE.name


def test_order_granted_refund_with_transaction_events(
    app,
    app_api_client,
    permission_manage_orders,
    permission_manage_shipping,
    permission_manage_users,
    fulfilled_order,
    transaction_item_generator,
):
    # given
    order = fulfilled_order
    charged_value = Decimal("10.0")
    transaction = transaction_item_generator(
        order_id=order.pk, charged_value=charged_value
    )
    granted_refund = order.granted_refunds.create(
        amount_value=Decimal("10.0"),
        currency="USD",
        reason="Test reason",
        app=app,
        shipping_costs_included=True,
        transaction_item=transaction,
    )
    event = transaction.events.create(
        psp_reference="123",
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=charged_value,
        include_in_calculations=True,
        currency=transaction.currency,
        related_granted_refund=granted_refund,
    )

    app_api_client.app.permissions.set(
        [permission_manage_orders, permission_manage_shipping, permission_manage_users]
    )

    # when
    response = app_api_client.post_graphql(ORDERS_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    granted_refunds = order_data["grantedRefunds"]
    assert len(granted_refunds) == 1
    grant_refund = granted_refunds[0]
    assert len(grant_refund["transactionEvents"]) == 1
    event_data = grant_refund["transactionEvents"][0]
    assert event_data["id"] == graphene.Node.to_global_id("TransactionEvent", event.id)
