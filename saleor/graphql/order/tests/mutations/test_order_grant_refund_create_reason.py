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


def test_grant_refund_with_reference_required_created_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
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

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

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
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_from_db = order.granted_refunds.first()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]

    assert (
        granted_refund_assigned_to_order["reasonReference"]["id"]
        == page_id
        == to_global_id_or_none(granted_refund_from_db.reason_reference)
    )
    assert granted_refund_from_db.reason_reference == page


def test_grant_refund_with_reference_required_but_not_provided_created_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

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
            "reason": "Damaged product refund",
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.REQUIRED.name
    assert (
        error["message"]
        == "Reason reference is required when refund reason reference type is "
        "configured."
    )

    assert order.granted_refunds.count() == 0


def test_grant_refund_with_reference_required_but_not_provided_created_by_app(
    app_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    app_api_client.app.permissions.set([permission_manage_orders])

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
            "reason": "Damaged product refund",
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_from_db = order.granted_refunds.first()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]

    assert granted_refund_assigned_to_order["reasonReference"] is None
    assert granted_refund_from_db.reason_reference is None


def test_grant_refund_with_reference_not_enabled_created_by_user_rejected(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
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

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

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
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]

    assert len(errors) == 1

    error = errors[0]

    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert error["message"] == "Reason reference type is not configured."


def test_grant_refund_with_reference_not_enabled_created_by_app_rejects(
    app_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
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

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page)
    app_api_client.app.permissions.set([permission_manage_orders])

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
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert error["message"] == "Reason reference type is not configured."


def test_grant_refund_with_reference_required_created_by_user_throws_for_invalid_id(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    invalid_page_id = graphene.Node.to_global_id("Page", 99999)
    assert Page.objects.count() == 0

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert (
        error["message"]
        == "Invalid reason reference. Must be an ID of a Page with the configured "
        "PageType."
    )

    assert order.granted_refunds.count() == 0


def test_grant_refund_with_reason_reference_wrong_page_type_created_by_user(
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

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    wrong_page_id = to_global_id_or_none(page_wrong_type)

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": wrong_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert (
        error["message"]
        == "Invalid reason reference. Must be an ID of a Page with the configured "
        "PageType."
    )

    assert order.granted_refunds.count() == 0


def test_grant_refund_with_reason_reference_not_valid_page_id(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    invalid_page_id = graphene.Node.to_global_id("Product", 12345)

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]

    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.GRAPHQL_ERROR.name
    assert (
        error["message"]
        == "Invalid reason reference. Must be an ID of a Page with the configured "
        "PageType."
    )

    assert order.granted_refunds.count() == 0


def test_grant_refund_with_reason_reference_not_valid_id_created_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    # Use a completely invalid ID format
    invalid_id = "invalid-id-format"

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.GRAPHQL_ERROR.name
    assert (
        error["message"]
        == "Invalid reason reference. Must be an ID of a Page with the configured "
        "PageType."
    )

    assert order.granted_refunds.count() == 0
