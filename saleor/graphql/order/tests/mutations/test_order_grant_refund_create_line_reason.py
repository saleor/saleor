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
      createdAt
      updatedAt
      amount{
        amount
      }
      reason
      reasonReference { id }
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
    order{
      id
      chargeStatus
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


def test_grant_refund_with_per_line_reason_reference(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
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
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    charged_amount = Decimal("20.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "lines": [
                {
                    "id": to_global_id_or_none(first_line),
                    "quantity": 1,
                    "reason": "Line reason",
                    "reasonReference": page_id,
                },
            ],
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    granted_refund = data["grantedRefund"]
    assert len(granted_refund["lines"]) == 1
    line_data = granted_refund["lines"][0]
    assert line_data["reason"] == "Line reason"
    assert line_data["reasonReference"]["id"] == page_id

    granted_refund_from_db = order.granted_refunds.first()
    granted_refund_line = granted_refund_from_db.lines.first()
    assert granted_refund_line.reason_reference == page


def test_grant_refund_with_per_line_reason_reference_omitted_when_configured(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
    site_settings,
):
    # given - per-line reason reference is always optional, even for staff
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
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    charged_amount = Decimal("20.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "lines": [
                {
                    "id": to_global_id_or_none(first_line),
                    "quantity": 1,
                    "reason": "Line reason",
                },
            ],
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    granted_refund = data["grantedRefund"]
    line_data = granted_refund["lines"][0]
    assert line_data["reasonReference"] is None

    granted_refund_from_db = order.granted_refunds.first()
    granted_refund_line = granted_refund_from_db.lines.first()
    assert granted_refund_line.reason_reference is None


def test_grant_refund_with_per_line_reason_reference_wrong_page_type(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
    site_settings,
):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    wrong_page_type = PageType.objects.create(name="Blog Posts", slug="blog-posts")
    page = Page.objects.create(
        slug="blog-post",
        title="Blog Post",
        page_type=wrong_page_type,
        is_published=True,
    )
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order = order_with_lines
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    page_id = to_global_id_or_none(page)
    valid_page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    valid_page_id = to_global_id_or_none(valid_page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    charged_amount = Decimal("20.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "lines": [
                {
                    "id": to_global_id_or_none(first_line),
                    "quantity": 1,
                    "reasonReference": page_id,
                },
            ],
            "reasonReference": valid_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == "Invalid reason reference. Must be an ID of a Page with the configured "
        "PageType."
    )


def test_grant_refund_with_per_line_reason_reference_when_not_configured(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
    site_settings,
):
    # given - no refund_reason_reference_type configured
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    order = order_with_lines
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    charged_amount = Decimal("20.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "lines": [
                {
                    "id": to_global_id_or_none(first_line),
                    "quantity": 1,
                    "reasonReference": page_id,
                },
            ],
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert errors[0]["message"] == "Reason reference type is not configured."
