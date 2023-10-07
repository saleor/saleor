import graphene

from .....payment import ChargeStatus, TransactionKind
from ....tests.utils import assert_no_permission, get_graphql_content

VOID_QUERY = """
    mutation PaymentVoid($paymentId: ID!) {
        paymentVoid(paymentId: $paymentId) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_payment_void_success(
    staff_api_client, permission_group_manage_orders, payment_txn_preauth
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}

    # when
    response = staff_api_client.post_graphql(VOID_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.is_active is False
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID


def test_payment_void_success_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    payment_txn_preauth,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    order = payment_txn_preauth.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}

    # when
    response = staff_api_client.post_graphql(VOID_QUERY, variables)

    # then
    assert_no_permission(response)


def test_payment_void_success_by_app(
    app_api_client, permission_manage_orders, payment_txn_preauth
):
    # given
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}

    # when
    response = app_api_client.post_graphql(
        VOID_QUERY, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.is_active is False
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID


def test_payment_void_gateway_error(
    staff_api_client, permission_group_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)

    # when
    response = staff_api_client.post_graphql(VOID_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert data["errors"]
    assert data["errors"][0]["field"] is None
    assert data["errors"][0]["message"] == "Unable to void the transaction."
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    assert payment_txn_preauth.is_active is True
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID
    assert not txn.is_success
