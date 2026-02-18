from decimal import Decimal

import graphene
import pytest

from .....order import OrderGrantedRefundStatus
from .....page.models import Page, PageType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from ...enums import (
    OrderGrantRefundUpdateErrorCode,
)

ORDER_GRANT_REFUND_UPDATE = """
mutation OrderGrantRefundUpdate(
    $id: ID!, $input: OrderGrantRefundUpdateInput!
){
  orderGrantRefundUpdate(id: $id, input:$input) {
    grantedRefund {
      id
      createdAt
      updatedAt
      amount {
        amount
      }
      reason
      reasonReference { id }
      user {
        id
      }
      app {
        id
      }
      shippingCostsIncluded
      lines{
        id
        orderLine{
          id
        }
        quantity
        reason
      }
      status
      transactionEvents{
        id
      }
      transaction{
        id
      }
    }
    order {
      id
      grantedRefunds{
        id
        amount{
          amount
        }
        createdAt
        updatedAt
        reason
        reasonReference { id }
        app{
          id
        }
        user{
          id
        }
        shippingCostsIncluded
        lines{
          id
          orderLine{
            id
          }
          quantity
          reason
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
    errors {
      field
      code
      message
      addLines{
        field
        code
        lineId
        message
      }
      removeLines{
        field
        code
        lineId
        message
      }
    }
  }
}

"""


@pytest.mark.parametrize("reason", ["", "new reason"])
def test_grant_refund_update_only_reason_by_user(
    reason, staff_api_client, app, permission_manage_orders, order
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {
        "id": granted_refund_id,
        "input": {"reason": reason},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund.refresh_from_db()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    assert granted_refund_assigned_to_order["reason"] == reason == granted_refund.reason
    assert granted_refund.amount_value == current_amount


@pytest.mark.parametrize("reason", ["", "new reason"])
def test_grant_refund_update_only_reason_by_app(
    reason, app_api_client, staff_user, permission_manage_orders, order
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    variables = {
        "id": granted_refund_id,
        "input": {"reason": reason},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund.refresh_from_db()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    assert granted_refund_assigned_to_order["reason"] == reason == granted_refund.reason
    assert granted_refund.amount_value == current_amount


@pytest.mark.parametrize(
    "granted_refund_status",
    [OrderGrantedRefundStatus.SUCCESS, OrderGrantedRefundStatus.PENDING],
)
def test_granted_refund_updated_when_status_blocks_action_and_only_reason_provided(
    granted_refund_status,
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
        status=granted_refund_status,
        transaction_item=transaction_item,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)

    app_api_client.app.permissions.set([permission_manage_orders])

    expected_reason = "New reason"
    variables = {
        "id": granted_refund_id,
        "input": {"reason": expected_reason},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]

    assert granted_refund.reason == expected_reason
    assert granted_refund_data["reason"] == expected_reason


def test_grant_refund_update_with_reference_required_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
    app,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    current_reason = "Original reason"
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("15.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert not errors

    order_id = to_global_id_or_none(order)
    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund.refresh_from_db()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]

    assert (
        granted_refund_assigned_to_order["reasonReference"]["id"]
        == page_id
        == to_global_id_or_none(granted_refund.reason_reference)
    )
    assert granted_refund.reason_reference == page


def test_grant_refund_update_with_reference_required_but_not_provided_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
    app,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    current_reason = "Original reason"
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("15.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.REQUIRED.name

    granted_refund.refresh_from_db()
    assert granted_refund.amount_value == current_amount
    assert granted_refund.reason == current_reason


def test_grant_refund_update_with_reference_required_but_not_provided_by_app(
    app_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
    staff_user,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    current_reason = "Original reason"
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    amount = Decimal("15.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            # "reasonReference": page_id,  # Not provided
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert not errors

    order_id = to_global_id_or_none(order)
    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund.refresh_from_db()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]

    assert granted_refund_assigned_to_order["reasonReference"] is None
    assert granted_refund.reason_reference is None


def test_grant_refund_update_with_reference_not_enabled_by_user_rejects(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
    app,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    assert site_settings.refund_reason_reference_type is None

    current_reason = "Original reason"
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("15.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name


def test_grant_refund_update_with_reference_not_enabled_by_app_rejects(
    app_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
    staff_user,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    assert site_settings.refund_reason_reference_type is None

    current_reason = "Original reason"
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    page_id = to_global_id_or_none(page)
    app_api_client.app.permissions.set([permission_manage_orders])

    amount = Decimal("15.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name


def test_grant_refund_update_with_reference_required_by_user_throws_for_invalid_id(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
    app,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    current_reason = "Original reason"
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("15.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    invalid_page_id = graphene.Node.to_global_id("Page", 99999)

    assert Page.objects.count() == 0

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name

    granted_refund.refresh_from_db()
    assert granted_refund.amount_value == current_amount
    assert granted_refund.reason == current_reason


def test_grant_refund_update_with_reason_reference_wrong_page_type_created_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type1 = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type1
    site_settings.save()

    page_type2 = PageType.objects.create(name="Different Type", slug="different-type")
    page_wrong_type = Page.objects.create(
        slug="wrong-type-page",
        title="Wrong Type Page",
        page_type=page_type2,
        is_published=True,
    )

    charged_value = Decimal("10.00")
    transaction_item = transaction_item_generator(
        order_id=order.id, charged_value=charged_value
    )

    current_reason = "Original reason."
    current_amount = Decimal("5.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_api_client.user,
        transaction_item=transaction_item,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    wrong_page_id = to_global_id_or_none(page_wrong_type)

    variables = {
        "id": granted_refund_id,
        "input": {
            "reason": "Updated reason with wrong page type",
            "reasonReference": wrong_page_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name

    granted_refund.refresh_from_db()
    assert granted_refund.amount_value == current_amount
    assert granted_refund.reason == current_reason


def test_grant_refund_update_with_reason_reference_not_valid_page_id(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
    app,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    current_reason = "Original reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("15.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    invalid_page_id = graphene.Node.to_global_id("Product", 12345)

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == "GRAPHQL_ERROR"

    granted_refund.refresh_from_db()
    assert granted_refund.amount_value == current_amount
    assert granted_refund.reason == current_reason


def test_grant_refund_update_with_reason_reference_not_valid_id(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
    app,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    current_reason = "Original reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("15.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    invalid_id = "invalid-id-format"

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == "GRAPHQL_ERROR"

    granted_refund.refresh_from_db()
    assert granted_refund.amount_value == current_amount
    assert granted_refund.reason == current_reason
