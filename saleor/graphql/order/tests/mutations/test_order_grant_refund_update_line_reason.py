from decimal import Decimal

import graphene

from .....page.models import Page, PageType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from ...enums import OrderGrantRefundUpdateErrorCode

ORDER_GRANT_REFUND_UPDATE = """
mutation OrderGrantRefundUpdate(
    $id: ID!, $input: OrderGrantRefundUpdateInput!
){
  orderGrantRefundUpdate(id: $id, input:$input) {
    grantedRefund {
      id
      amount {
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
      addLines{
        field
        code
        lineId
        message
      }
    }
  }
}
"""


def test_add_line_with_reason_reference(
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

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )

    granted_refund = order.granted_refunds.create(
        amount_value=amount,
        currency=order.currency,
        reason="Original reason",
        reason_reference=page,
        user=staff_api_client.user,
        transaction_item=transaction_item,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    page_id = to_global_id_or_none(page)

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    variables = {
        "id": granted_refund_id,
        "input": {
            "reasonReference": page_id,
            "addLines": [
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
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    granted_refund_data = data["grantedRefund"]
    assert len(granted_refund_data["lines"]) == 1

    refund_line = granted_refund_data["lines"][0]
    assert refund_line["reason"] == "Line damaged"
    assert refund_line["reasonReference"]["id"] == page_id

    refund_line_from_db = granted_refund.lines.first()
    assert refund_line_from_db.reason_reference == page


def test_add_line_with_reason_reference_wrong_page_type(
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
    page_correct = Page.objects.create(
        slug="correct-page",
        title="Correct Page",
        page_type=page_type_configured,
        is_published=True,
    )

    page_type_other = PageType.objects.create(name="Other Type", slug="other-type")
    page_wrong = Page.objects.create(
        slug="wrong-page",
        title="Wrong Page",
        page_type=page_type_other,
        is_published=True,
    )

    site_settings.refund_reason_reference_type = page_type_configured
    site_settings.save(update_fields=["refund_reason_reference_type"])

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )

    granted_refund = order.granted_refunds.create(
        amount_value=amount,
        currency=order.currency,
        reason="Original reason",
        reason_reference=page_correct,
        user=staff_api_client.user,
        transaction_item=transaction_item,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    correct_page_id = to_global_id_or_none(page_correct)
    wrong_page_id = to_global_id_or_none(page_wrong)

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    variables = {
        "id": granted_refund_id,
        "input": {
            "reasonReference": correct_page_id,
            "addLines": [
                {
                    "id": line_id,
                    "quantity": 1,
                    "reason": "Line damaged",
                    "reasonReference": wrong_page_id,
                }
            ],
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == "Invalid reason reference. Must be an ID of a Model (Page)"
    )


def test_add_line_with_reason_reference_not_configured(
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

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )

    granted_refund = order.granted_refunds.create(
        amount_value=amount,
        currency=order.currency,
        reason="Original reason",
        user=staff_api_client.user,
        transaction_item=transaction_item,
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    page_id = to_global_id_or_none(page)

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    variables = {
        "id": granted_refund_id,
        "input": {
            "addLines": [
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
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderGrantRefundUpdateErrorCode.NOT_CONFIGURED.name
    assert errors[0]["message"] == "Reason reference type is not configured."
