import graphene

from .....order.error_codes import OrderErrorCode
from .....order.models import FulfillmentStatus
from .....page.models import Page, PageType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from .test_fulfillment_return_products import ORDER_FULFILL_RETURN_MUTATION

ORDER_FULFILLMENT_REASONS_QUERY = """
query Order($id: ID!) {
    order(id: $id) {
        fulfillments {
            status
            reason
            reasonReference { id }
            lines {
                reason
                reasonReference { id }
            }
        }
    }
}
"""


def test_fulfillment_return_products_with_global_reason_and_reason_reference(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.pk)
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)
    page_id = to_global_id_or_none(page)
    reason = "Global return reason"

    variables = {
        "order": order_id,
        "input": {
            "orderLines": [
                {
                    "orderLineId": line_id,
                    "quantity": 1,
                    "replace": False,
                },
            ],
            "reason": reason,
            "reasonReference": page_id,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    assert not data["errors"]

    return_fulfillment = data["returnFulfillment"]
    assert return_fulfillment["status"] == FulfillmentStatus.RETURNED.upper()
    assert len(return_fulfillment["lines"]) == 1

    order.refresh_from_db()
    fulfillment = order.fulfillments.get(status=FulfillmentStatus.RETURNED)
    assert fulfillment.reason == reason
    assert fulfillment.reason_reference == page


def test_fulfillment_return_products_staff_omits_reason_reference_when_configured(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given - global reasonReference is required for staff when configured
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.pk)
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    variables = {
        "order": order_id,
        "input": {
            "orderLines": [
                {
                    "orderLineId": line_id,
                    "quantity": 1,
                    "replace": False,
                },
            ],
            "reason": "Return reason without reference",
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderErrorCode.REQUIRED.name
    assert (
        errors[0]["message"]
        == "Reason reference is required when reason reference type is configured."
    )


def test_fulfillment_return_products_with_per_line_reason(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.pk)
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)
    page_id = to_global_id_or_none(page)
    line_reason = "Per-line reason"

    variables = {
        "order": order_id,
        "input": {
            "orderLines": [
                {
                    "orderLineId": line_id,
                    "quantity": 1,
                    "replace": False,
                    "reason": line_reason,
                    "reasonReference": page_id,
                },
            ],
            "reasonReference": page_id,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    assert not data["errors"]

    order.refresh_from_db()
    fulfillment = order.fulfillments.get(status=FulfillmentStatus.RETURNED)
    fulfillment_line = fulfillment.lines.first()
    assert fulfillment_line.reason == line_reason
    assert fulfillment_line.reason_reference == page


def test_fulfillment_return_products_per_line_reason_reference_when_not_configured(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given - no return_reason_reference_type configured; per-line ref is an error
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.pk)
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)
    page_id = to_global_id_or_none(page)

    variables = {
        "order": order_id,
        "input": {
            "orderLines": [
                {
                    "orderLineId": line_id,
                    "quantity": 1,
                    "replace": False,
                    "reasonReference": page_id,
                },
            ],
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert errors[0]["message"] == "Reason reference type is not configured."


def test_fulfillment_return_products_per_line_reason_reference_wrong_page_type(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
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
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.pk)
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    variables = {
        "order": order_id,
        "input": {
            "orderLines": [
                {
                    "orderLineId": line_id,
                    "quantity": 1,
                    "replace": False,
                    "reasonReference": to_global_id_or_none(wrong_page),
                },
            ],
            "reasonReference": to_global_id_or_none(valid_page),
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "reasonReference"
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == "Invalid reason reference. Must be an ID of a Model (Page)"
    )


def test_fulfillment_return_products_reason_fields_resolve(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given - return with a global reason and a per-line reason/reasonReference
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.pk)
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)
    page_id = to_global_id_or_none(page)
    global_reason = "Global return reason"
    line_reason = "Per-line reason"
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    return_response = staff_api_client.post_graphql(
        ORDER_FULFILL_RETURN_MUTATION,
        {
            "order": order_id,
            "input": {
                "orderLines": [
                    {
                        "orderLineId": line_id,
                        "quantity": 1,
                        "replace": False,
                        "reason": line_reason,
                        "reasonReference": page_id,
                    },
                ],
                "reason": global_reason,
                "reasonReference": page_id,
            },
        },
    )
    assert not get_graphql_content(return_response)["data"][
        "orderFulfillmentReturnProducts"
    ]["errors"]

    # when - the reason fields are resolved through GraphQL
    response = staff_api_client.post_graphql(
        ORDER_FULFILLMENT_REASONS_QUERY, {"id": order_id}
    )

    # then
    content = get_graphql_content(response)
    fulfillments = content["data"]["order"]["fulfillments"]
    returned = next(
        f for f in fulfillments if f["status"] == FulfillmentStatus.RETURNED.upper()
    )
    assert returned["reason"] == global_reason
    assert returned["reasonReference"]["id"] == page_id
    returned_line = returned["lines"][0]
    assert returned_line["reason"] == line_reason
    assert returned_line["reasonReference"]["id"] == page_id
