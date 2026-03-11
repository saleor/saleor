from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from django.utils import timezone

from .....graphql.tests.utils import get_graphql_content
from .....order.error_codes import OrderErrorCode
from .....payment import ChargeStatus, CustomPaymentChoices
from .....payment.models import Payment

ORDER_OVERRIDE_DEPOSIT_THRESHOLD_MUTATION = """
    mutation overrideDepositThreshold($id: ID!, $override: Boolean!) {
        orderOverrideDepositThreshold(id: $id, override: $override) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
        }
    }
"""

ORDER_SET_DEPOSIT_REQUIRED_MUTATION = """
    mutation setDeposit(
        $id: ID!, $required: Boolean!, $percentage: Decimal,
        $xeroBankAccountCode: String,
        $xeroBankAccountSortCode: String,
        $xeroBankAccountNumber: String
    ) {
        orderSetDepositRequired(
            id: $id, required: $required, percentage: $percentage,
            xeroBankAccountCode: $xeroBankAccountCode,
            xeroBankAccountSortCode: $xeroBankAccountSortCode,
            xeroBankAccountNumber: $xeroBankAccountNumber
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
                depositRequired
                depositPercentage
                xeroBankAccountCode
                xeroBankAccountSortCode
                xeroBankAccountNumber
            }
        }
    }
"""

ORDER_ADD_PREPAYMENT_MUTATION = """
    mutation addPrepayment(
        $orderId: ID!, $pspReference: String!, $fulfillmentId: ID
    ) {
        orderAddPrepayment(
            orderId: $orderId, pspReference: $pspReference,
            fulfillmentId: $fulfillmentId
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
        }
    }
"""

ORDER_CHECK_PREPAYMENT_MUTATION = """
    mutation checkPrepayment($orderId: ID!, $pspReference: String!) {
        orderCheckPrepayment(orderId: $orderId, pspReference: $pspReference) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
        }
    }
"""

ORDER_DELETE_PREPAYMENT_MUTATION = """
    mutation deletePrepayment($orderId: ID!, $pspReference: String!) {
        orderDeletePrepayment(orderId: $orderId, pspReference: $pspReference) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
        }
    }
"""


# --- OrderSetDepositRequired ---


def test_order_set_deposit_required(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)

    response = staff_api_client.post_graphql(
        ORDER_SET_DEPOSIT_REQUIRED_MUTATION,
        {
            "id": order_id,
            "required": True,
            "percentage": 30.0,
            "xeroBankAccountCode": "090",
            "xeroBankAccountSortCode": "123456",
            "xeroBankAccountNumber": "12345678",
        },
    )

    content = get_graphql_content(response)
    data = content["data"]["orderSetDepositRequired"]
    assert not data["errors"]
    assert data["order"]["depositRequired"] is True
    assert float(data["order"]["depositPercentage"]) == 30.0
    assert data["order"]["xeroBankAccountCode"] == "090"
    assert data["order"]["xeroBankAccountSortCode"] == "123456"
    assert data["order"]["xeroBankAccountNumber"] == "12345678"

    order.refresh_from_db()
    assert order.deposit_required is True
    assert order.deposit_percentage == Decimal("30.0")
    assert order.xero_bank_account_code == "090"
    assert order.xero_bank_account_sort_code == "123456"
    assert order.xero_bank_account_number == "12345678"


def test_order_set_deposit_required_without_bank_account_fails(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)

    response = staff_api_client.post_graphql(
        ORDER_SET_DEPOSIT_REQUIRED_MUTATION,
        {"id": order_id, "required": True, "percentage": 30.0},
    )

    content = get_graphql_content(response)
    errors = content["data"]["orderSetDepositRequired"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "xeroBankAccountCode"
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


def test_order_set_deposit_not_required_clears_bank_account(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.deposit_required = True
    order.xero_bank_account_code = "090"
    order.xero_bank_account_sort_code = "123456"
    order.xero_bank_account_number = "12345678"
    order.save(
        update_fields=[
            "deposit_required",
            "xero_bank_account_code",
            "xero_bank_account_sort_code",
            "xero_bank_account_number",
        ]
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    response = staff_api_client.post_graphql(
        ORDER_SET_DEPOSIT_REQUIRED_MUTATION,
        {"id": order_id, "required": False},
    )

    content = get_graphql_content(response)
    data = content["data"]["orderSetDepositRequired"]
    assert not data["errors"]
    assert data["order"]["depositRequired"] is False
    assert data["order"]["xeroBankAccountCode"] is None
    assert data["order"]["xeroBankAccountSortCode"] is None
    assert data["order"]["xeroBankAccountNumber"] is None

    order.refresh_from_db()
    assert order.xero_bank_account_code is None
    assert order.xero_bank_account_sort_code is None
    assert order.xero_bank_account_number is None


def test_order_set_deposit_required_blocked_with_unpaid_deposit_prepayments(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.deposit_required = True
    order.deposit_percentage = Decimal(30)
    order.xero_bank_account_code = "090"
    order.save(
        update_fields=[
            "deposit_required",
            "deposit_percentage",
            "xero_bank_account_code",
        ]
    )
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="deposit-prepayment-uuid",
        total=Decimal(0),
        captured_amount=Decimal(0),
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
        fulfillment=None,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_SET_DEPOSIT_REQUIRED_MUTATION,
        {
            "id": order_id,
            "required": True,
            "percentage": 50.0,
            "xeroBankAccountCode": "090",
        },
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderSetDepositRequired"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


@pytest.mark.parametrize(
    ("percentage", "should_error"),
    [
        (-10, True),
        (150, True),
        (0, False),
        (100, False),
        (50.5, False),
    ],
)
def test_order_set_deposit_required_percentage_validation(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    percentage,
    should_error,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)

    response = staff_api_client.post_graphql(
        ORDER_SET_DEPOSIT_REQUIRED_MUTATION,
        {
            "id": order_id,
            "required": True,
            "percentage": percentage,
            "xeroBankAccountCode": "090",
        },
    )

    content = get_graphql_content(response)
    errors = content["data"]["orderSetDepositRequired"]["errors"]
    assert bool(errors) == should_error
    if should_error:
        assert errors[0]["code"] == OrderErrorCode.INVALID.name


# --- OrderOverrideDepositThreshold ---


def test_order_override_deposit_threshold_sets_deposit_paid_at(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.deposit_required = True
    order.deposit_percentage = Decimal(50)
    order.save(update_fields=["deposit_required", "deposit_percentage"])
    assert order.deposit_paid_at is None

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_OVERRIDE_DEPOSIT_THRESHOLD_MUTATION,
        {"id": order_id, "override": True},
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderOverrideDepositThreshold"]["errors"]
    order.refresh_from_db()
    assert order.deposit_threshold_met_override is True
    assert order.deposit_paid_at is not None


def test_order_override_deposit_threshold_does_not_overwrite_existing_deposit_paid_at(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.deposit_required = True
    order.deposit_percentage = Decimal(50)
    existing_ts = timezone.now()
    order.deposit_paid_at = existing_ts
    order.save(
        update_fields=["deposit_required", "deposit_percentage", "deposit_paid_at"]
    )

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_OVERRIDE_DEPOSIT_THRESHOLD_MUTATION,
        {"id": order_id, "override": True},
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderOverrideDepositThreshold"]["errors"]
    order.refresh_from_db()
    assert order.deposit_paid_at == existing_ts


def test_order_override_deposit_threshold_false_does_not_clear_deposit_paid_at(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.deposit_required = True
    order.deposit_percentage = Decimal(50)
    order.deposit_threshold_met_override = True
    existing_ts = timezone.now()
    order.deposit_paid_at = existing_ts
    order.save(
        update_fields=[
            "deposit_required",
            "deposit_percentage",
            "deposit_threshold_met_override",
            "deposit_paid_at",
        ]
    )

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_OVERRIDE_DEPOSIT_THRESHOLD_MUTATION,
        {"id": order_id, "override": False},
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderOverrideDepositThreshold"]["errors"]
    order.refresh_from_db()
    assert order.deposit_threshold_met_override is False
    assert order.deposit_paid_at == existing_ts


def test_order_override_deposit_threshold_requires_deposit(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    assert order.deposit_required is False
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_OVERRIDE_DEPOSIT_THRESHOLD_MUTATION,
        {"id": order_id, "override": True},
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderOverrideDepositThreshold"]["errors"]
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


def test_order_override_deposit_threshold_blocked_with_unpaid_deposit_prepayments(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.deposit_required = True
    order.deposit_percentage = Decimal(50)
    order.save(update_fields=["deposit_required", "deposit_percentage"])
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="deposit-prepayment-uuid",
        total=Decimal(0),
        captured_amount=Decimal(0),
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
        fulfillment=None,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_OVERRIDE_DEPOSIT_THRESHOLD_MUTATION,
        {"id": order_id, "override": True},
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderOverrideDepositThreshold"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


# --- OrderAddPrepayment ---

XERO_UNPAID = {"reconciledAmount": "0.00", "currency": "GBP"}
XERO_MOCK_PATH = "saleor.plugins.manager.PluginsManager.xero_check_prepayment_status"


def test_add_deposit_prepayment(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given - order with no fulfillments
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    with patch(XERO_MOCK_PATH, return_value=XERO_UNPAID):
        response = staff_api_client.post_graphql(
            ORDER_ADD_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "deposit-pp-001"},
        )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderAddPrepayment"]["errors"]
    payment = Payment.objects.get(psp_reference="deposit-pp-001")
    assert payment.order == order
    assert payment.fulfillment is None
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.gateway == CustomPaymentChoices.XERO
    assert payment.captured_amount == Decimal(0)

    order.refresh_from_db()
    assert order.total_charged_amount == Decimal(0)


def test_add_deposit_prepayment_already_paid_in_xero(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when - Xero reports the prepayment is already reconciled
    xero_paid = {"reconciledAmount": "150.00", "currency": "GBP"}
    with patch(XERO_MOCK_PATH, return_value=xero_paid):
        response = staff_api_client.post_graphql(
            ORDER_ADD_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "deposit-pp-paid"},
        )

    # then - payment is created and marked as paid
    content = get_graphql_content(response)
    assert not content["data"]["orderAddPrepayment"]["errors"]
    payment = Payment.objects.get(psp_reference="deposit-pp-paid")
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == Decimal("150.00")
    assert payment.total == Decimal("150.00")

    order.refresh_from_db()
    assert order.total_charged_amount == Decimal("150.00")


def test_add_prepayment_not_found_in_xero(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)

    # when - Xero returns None (bank transaction doesn't exist)
    with patch(XERO_MOCK_PATH, return_value=None):
        response = staff_api_client.post_graphql(
            ORDER_ADD_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "bogus-ref"},
        )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderAddPrepayment"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert "not found" in errors[0]["message"].lower()
    assert not Payment.objects.filter(psp_reference="bogus-ref").exists()


def test_add_proforma_prepayment_with_fulfillment(
    staff_api_client, permission_group_manage_orders, fulfilled_order
):
    # given - order with fulfillments
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = fulfilled_order
    fulfillment = order.fulfillments.first()
    order_id = graphene.Node.to_global_id("Order", order.id)
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.id)

    # when
    with patch(XERO_MOCK_PATH, return_value=XERO_UNPAID):
        response = staff_api_client.post_graphql(
            ORDER_ADD_PREPAYMENT_MUTATION,
            {
                "orderId": order_id,
                "pspReference": "proforma-pp-001",
                "fulfillmentId": fulfillment_id,
            },
        )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderAddPrepayment"]["errors"]
    payment = Payment.objects.get(psp_reference="proforma-pp-001")
    assert payment.order == order
    assert payment.fulfillment == fulfillment
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


def test_add_prepayment_requires_fulfillment_id_when_fulfillments_exist(
    staff_api_client, permission_group_manage_orders, fulfilled_order
):
    # given - order with fulfillments but no fulfillment_id provided
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = fulfilled_order
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_ADD_PREPAYMENT_MUTATION,
        {"orderId": order_id, "pspReference": "deposit-pp-blocked"},
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderAddPrepayment"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert "fulfillment" in errors[0]["message"].lower()


def test_add_prepayment_rejects_fulfillment_id_when_no_fulfillments(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given - order has no fulfillments but fulfillment_id is provided
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    assert not order.fulfillments.exists()
    order_id = graphene.Node.to_global_id("Order", order.id)
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", 99999)

    # when
    response = staff_api_client.post_graphql(
        ORDER_ADD_PREPAYMENT_MUTATION,
        {
            "orderId": order_id,
            "pspReference": "proforma-pp-blocked",
            "fulfillmentId": fulfillment_id,
        },
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderAddPrepayment"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


def test_add_prepayment_duplicate_psp_reference_fails(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="existing-pp-ref",
        total=Decimal(0),
        captured_amount=Decimal(0),
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_ADD_PREPAYMENT_MUTATION,
        {"orderId": order_id, "pspReference": "existing-pp-ref"},
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderAddPrepayment"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert "already exists" in errors[0]["message"].lower()


# --- OrderDeletePrepayment ---


def test_delete_unpaid_prepayment(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="pp-to-delete",
        total=Decimal(0),
        captured_amount=Decimal(0),
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when - Xero returns None (bank transaction deleted)
    with patch(XERO_MOCK_PATH, return_value=None):
        response = staff_api_client.post_graphql(
            ORDER_DELETE_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "pp-to-delete"},
        )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderDeletePrepayment"]["errors"]
    assert not Payment.objects.filter(psp_reference="pp-to-delete").exists()


def test_delete_prepayment_blocked_when_paid(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="pp-paid",
        total=Decimal("100.00"),
        captured_amount=Decimal("100.00"),
        charge_status=ChargeStatus.FULLY_CHARGED,
        currency=order.currency,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_DELETE_PREPAYMENT_MUTATION,
        {"orderId": order_id, "pspReference": "pp-paid"},
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderDeletePrepayment"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert "already been paid" in errors[0]["message"].lower()


def test_delete_prepayment_blocked_when_still_in_xero(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="pp-still-in-xero",
        total=Decimal(0),
        captured_amount=Decimal(0),
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when - Xero returns non-None (prepayment still exists)
    with patch(XERO_MOCK_PATH, return_value=XERO_UNPAID):
        response = staff_api_client.post_graphql(
            ORDER_DELETE_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "pp-still-in-xero"},
        )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderDeletePrepayment"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert "void" in errors[0]["message"].lower()
    assert Payment.objects.filter(psp_reference="pp-still-in-xero").exists()


def test_delete_prepayment_not_found(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_DELETE_PREPAYMENT_MUTATION,
        {"orderId": order_id, "pspReference": "nonexistent-pp"},
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderDeletePrepayment"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name


# --- OrderCheckPrepayment ---


def test_check_prepayment_marks_paid_when_reconciled(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="pp-check-paid",
        total=Decimal(0),
        captured_amount=Decimal(0),
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    xero_paid = {"reconciledAmount": "200.00", "currency": "GBP"}
    with patch(XERO_MOCK_PATH, return_value=xero_paid):
        response = staff_api_client.post_graphql(
            ORDER_CHECK_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "pp-check-paid"},
        )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderCheckPrepayment"]["errors"]
    payment = Payment.objects.get(psp_reference="pp-check-paid")
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == Decimal("200.00")

    order.refresh_from_db()
    assert order.total_charged_amount == Decimal("200.00")


def test_check_prepayment_deletes_when_gone_from_xero(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="pp-check-gone",
        total=Decimal(0),
        captured_amount=Decimal(0),
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    with patch(XERO_MOCK_PATH, return_value=None):
        response = staff_api_client.post_graphql(
            ORDER_CHECK_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "pp-check-gone"},
        )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderCheckPrepayment"]["errors"]
    assert not Payment.objects.filter(psp_reference="pp-check-gone").exists()

    order.refresh_from_db()
    assert order.total_charged_amount == Decimal(0)


def test_check_prepayment_no_op_when_still_unpaid(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="pp-check-unpaid",
        total=Decimal(0),
        captured_amount=Decimal(0),
        charge_status=ChargeStatus.NOT_CHARGED,
        currency=order.currency,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    with patch(XERO_MOCK_PATH, return_value=XERO_UNPAID):
        response = staff_api_client.post_graphql(
            ORDER_CHECK_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "pp-check-unpaid"},
        )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderCheckPrepayment"]["errors"]
    payment = Payment.objects.get(psp_reference="pp-check-unpaid")
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


def test_check_prepayment_resets_to_unpaid_when_unreconciled(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given - payment was previously marked as paid
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    Payment.objects.create(
        order=order,
        gateway=CustomPaymentChoices.XERO,
        psp_reference="pp-already-paid",
        total=Decimal("100.00"),
        captured_amount=Decimal("100.00"),
        charge_status=ChargeStatus.FULLY_CHARGED,
        currency=order.currency,
    )
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when - Xero reports prepayment is no longer reconciled
    with patch(XERO_MOCK_PATH, return_value=XERO_UNPAID):
        response = staff_api_client.post_graphql(
            ORDER_CHECK_PREPAYMENT_MUTATION,
            {"orderId": order_id, "pspReference": "pp-already-paid"},
        )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderCheckPrepayment"]["errors"]
    payment = Payment.objects.get(psp_reference="pp-already-paid")
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.captured_amount == Decimal(0)
    assert payment.total == Decimal(0)

    order.refresh_from_db()
    assert order.total_charged_amount == Decimal(0)


def test_check_prepayment_not_found(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_CHECK_PREPAYMENT_MUTATION,
        {"orderId": order_id, "pspReference": "nonexistent"},
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderCheckPrepayment"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
