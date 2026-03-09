from decimal import Decimal

import graphene

from .....page.models import Page, PageType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from ...enums import OrderGrantRefundCreateErrorCode

ORDER_GRANT_REFUND_CREATE = """
mutation OrderGrantRefundCreate(
    $id: ID!, $input: OrderGrantRefundCreateInput!
){
  orderGrantRefundCreate(id: $id, input:$input){
    grantedRefund{
      id
      amount{
        amount
      }
      reason
      reasonReference { id }
      lines{
        id
        orderLine{
          id
        }
        quantity
        reason
        reasonReference { id }
      }
    }
    errors{
      field
      code
      message
      lines{
        field
        code
        lineId
        message
      }
    }
  }
}
"""


def test_with_per_line_reason_reference(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
    site_settings,
):
    # Given
    order = order_with_lines
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "transactionId": transaction_item_id,
            "reasonReference": page_id,
            "lines": [
                {
                    "id": line_id,
                    "quantity": 1,
                    "reason": "Line damaged",
                    "reasonReference": page_id,
                }
            ],
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    assert not data["errors"]

    granted_refund = data["grantedRefund"]
    assert len(granted_refund["lines"]) == 1

    refund_line = granted_refund["lines"][0]
    assert refund_line["reason"] == "Line damaged"
    assert refund_line["reasonReference"]["id"] == page_id

    granted_refund_line_from_db = order.granted_refunds.first().lines.first()
    assert granted_refund_line_from_db.reason_reference == page


def test_with_per_line_reason_reference_multiple_lines(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
    site_settings,
):
    # Given
    order = order_with_lines
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page1 = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    page2 = Page.objects.create(
        slug="wrong-size",
        title="Wrong Size",
        page_type=page_type,
        is_published=True,
    )

    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    page1_id = to_global_id_or_none(page1)
    page2_id = to_global_id_or_none(page2)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    lines = order.lines.all()
    line1_id = graphene.Node.to_global_id("OrderLine", lines[0].pk)
    line2_id = graphene.Node.to_global_id("OrderLine", lines[1].pk)

    amount = Decimal("20.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "transactionId": transaction_item_id,
            "reasonReference": page1_id,
            "lines": [
                {
                    "id": line1_id,
                    "quantity": 1,
                    "reason": "Damaged",
                    "reasonReference": page1_id,
                },
                {
                    "id": line2_id,
                    "quantity": 1,
                    "reason": "Wrong size",
                    "reasonReference": page2_id,
                },
            ],
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    assert not data["errors"]

    granted_refund = data["grantedRefund"]
    assert len(granted_refund["lines"]) == 2

    lines_by_reason = {line["reason"]: line for line in granted_refund["lines"]}
    assert lines_by_reason["Damaged"]["reasonReference"]["id"] == page1_id
    assert lines_by_reason["Wrong size"]["reasonReference"]["id"] == page2_id


def test_with_per_line_reason_reference_no_config_rejects(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
    site_settings,
):
    # Given - refund_reason_reference_type is NOT configured
    order = order_with_lines
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    assert site_settings.refund_reason_reference_type is None

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "transactionId": transaction_item_id,
            "lines": [
                {
                    "id": line_id,
                    "quantity": 1,
                    "reason": "Damaged",
                    "reasonReference": page_id,
                }
            ],
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderGrantRefundCreateErrorCode.NOT_CONFIGURED.name
    assert errors[0]["message"] == "Reason reference type is not configured."


def test_with_per_line_reason_reference_wrong_page_type(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
    site_settings,
):
    # Given
    order = order_with_lines
    page_type_configured = PageType.objects.create(
        name="Refund Reasons", slug="refund-reasons"
    )
    page_type_other = PageType.objects.create(name="Other Type", slug="other-type")
    page_wrong_type = Page.objects.create(
        slug="wrong-type-page",
        title="Wrong Type Page",
        page_type=page_type_other,
        is_published=True,
    )

    site_settings.refund_reason_reference_type = page_type_configured
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page_wrong_type)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    # Need a valid top-level reasonReference too
    page_correct = Page.objects.create(
        slug="correct-page",
        title="Correct Page",
        page_type=page_type_configured,
        is_published=True,
    )
    correct_page_id = to_global_id_or_none(page_correct)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "transactionId": transaction_item_id,
            "reasonReference": correct_page_id,
            "lines": [
                {
                    "id": line_id,
                    "quantity": 1,
                    "reason": "Damaged",
                    "reasonReference": page_id,
                }
            ],
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == "Invalid reason reference. Must be an ID of a Model (Page)"
    )


def test_line_without_reason_reference_when_not_configured(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
    site_settings,
):
    # Given - no refund_reason_reference_type configured, no reason_reference on line
    order = order_with_lines
    assert site_settings.refund_reason_reference_type is None

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "transactionId": transaction_item_id,
            "lines": [
                {
                    "id": line_id,
                    "quantity": 1,
                    "reason": "Damaged",
                }
            ],
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    assert not data["errors"]

    refund_line = data["grantedRefund"]["lines"][0]
    assert refund_line["reason"] == "Damaged"
    assert refund_line["reasonReference"] is None
