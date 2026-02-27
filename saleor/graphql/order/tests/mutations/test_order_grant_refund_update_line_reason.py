from decimal import Decimal

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
        reasonReference { id }
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


def test_grant_refund_update_add_lines_with_per_line_reason_reference(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order = order_with_lines
    granted_refund = order.granted_refunds.create(
        amount_value=Decimal("10.00"),
        currency=order.currency,
        reason="Reason",
        reason_reference=page,
        user=staff_api_client.user,
    )
    order_line = order.lines.first()
    page_id = to_global_id_or_none(page)
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    variables = {
        "id": granted_refund_id,
        "input": {
            "reasonReference": page_id,
            "addLines": [
                {
                    "id": to_global_id_or_none(order_line),
                    "quantity": 1,
                    "reason": "Line damage",
                    "reasonReference": page_id,
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    granted_refund_data = data["grantedRefund"]
    assert len(granted_refund_data["lines"]) == 1
    line_data = granted_refund_data["lines"][0]
    assert line_data["reason"] == "Line damage"
    assert line_data["reasonReference"]["id"] == page_id

    granted_refund_line = granted_refund.lines.first()
    assert granted_refund_line.reason_reference == page


def test_grant_refund_update_add_lines_without_per_line_reason_reference(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    site_settings,
):
    # given - per-line reason reference is always optional
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order = order_with_lines
    granted_refund = order.granted_refunds.create(
        amount_value=Decimal("10.00"),
        currency=order.currency,
        reason="Reason",
        reason_reference=page,
        user=staff_api_client.user,
    )
    order_line = order.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    page_id = to_global_id_or_none(page)
    variables = {
        "id": granted_refund_id,
        "input": {
            "reasonReference": page_id,
            "addLines": [
                {
                    "id": to_global_id_or_none(order_line),
                    "quantity": 1,
                    "reason": "Line damage",
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    granted_refund_data = data["grantedRefund"]
    line_data = granted_refund_data["lines"][0]
    assert line_data["reasonReference"] is None

    granted_refund_line = granted_refund.lines.first()
    assert granted_refund_line.reason_reference is None


def test_grant_refund_update_add_lines_with_wrong_page_type_reason_reference(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    wrong_page_type = PageType.objects.create(name="Blog Posts", slug="blog-posts")
    wrong_page = Page.objects.create(
        slug="blog-post",
        title="Blog Post",
        page_type=wrong_page_type,
        is_published=True,
    )
    valid_page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order = order_with_lines
    granted_refund = order.granted_refunds.create(
        amount_value=Decimal("10.00"),
        currency=order.currency,
        reason="Reason",
        reason_reference=valid_page,
        user=staff_api_client.user,
    )
    order_line = order.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    valid_page_id = to_global_id_or_none(valid_page)
    variables = {
        "id": granted_refund_id,
        "input": {
            "reasonReference": valid_page_id,
            "addLines": [
                {
                    "id": to_global_id_or_none(order_line),
                    "quantity": 1,
                    "reasonReference": to_global_id_or_none(wrong_page),
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == "Invalid reason reference. Must be an ID of a Page with the configured "
        "PageType."
    )
