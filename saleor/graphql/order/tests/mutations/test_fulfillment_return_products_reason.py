from unittest.mock import patch

import graphene

from .....order.error_codes import OrderErrorCode
from .....order.models import FulfillmentStatus
from .....page.models import Page, PageType
from .....payment import ChargeStatus
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


def test_fulfillment_return_products_fulfillment_lines_with_global_and_per_line_reasons(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    site_settings,
):
    # given - a return via fulfillmentLines with a global reason and distinct
    # per-line reasons on each fulfillment line
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    global_page = Page.objects.create(
        slug="customer-return",
        title="Customer return",
        page_type=page_type,
        is_published=True,
    )
    line_page_1 = Page.objects.create(
        slug="damaged", title="Damaged", page_type=page_type, is_published=True
    )
    line_page_2 = Page.objects.create(
        slug="wrong-size", title="Wrong size", page_type=page_type, is_published=True
    )
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = fulfilled_order
    order_id = graphene.Node.to_global_id("Order", order.pk)
    fulfillment = order.fulfillments.first()
    line_1 = fulfillment.lines.first()
    line_2 = fulfillment.lines.last()
    global_reason = "Customer return request"
    line_1_reason = "Item arrived damaged"
    line_2_reason = "Wrong size"

    variables = {
        "order": order_id,
        "input": {
            "refund": False,
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": to_global_id_or_none(line_1),
                    "quantity": 1,
                    "replace": False,
                    "reason": line_1_reason,
                    "reasonReference": to_global_id_or_none(line_page_1),
                },
                {
                    "fulfillmentLineId": to_global_id_or_none(line_2),
                    "quantity": 1,
                    "replace": False,
                    "reason": line_2_reason,
                    "reasonReference": to_global_id_or_none(line_page_2),
                },
            ],
            "reason": global_reason,
            "reasonReference": to_global_id_or_none(global_page),
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
    return_fulfillment = order.fulfillments.get(status=FulfillmentStatus.RETURNED)
    assert return_fulfillment.reason == global_reason
    assert return_fulfillment.reason_reference == global_page

    lines_by_order_line = {
        line.order_line_id: line for line in return_fulfillment.lines.all()
    }
    returned_line_1 = lines_by_order_line[line_1.order_line_id]
    returned_line_2 = lines_by_order_line[line_2.order_line_id]
    assert returned_line_1.reason == line_1_reason
    assert returned_line_1.reason_reference == line_page_1
    assert returned_line_2.reason == line_2_reason
    assert returned_line_2.reason_reference == line_page_2


def test_fulfillment_return_products_fulfillment_lines_mixed_per_line_reason(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    site_settings,
):
    # given - global reasonReference set; only one fulfillment line has a per-line
    # reference. The other line must store null (no inheritance from the global one).
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    global_page = Page.objects.create(
        slug="customer-return",
        title="Customer return",
        page_type=page_type,
        is_published=True,
    )
    line_page = Page.objects.create(
        slug="damaged", title="Damaged", page_type=page_type, is_published=True
    )
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = fulfilled_order
    order_id = graphene.Node.to_global_id("Order", order.pk)
    fulfillment = order.fulfillments.first()
    line_with_reason = fulfillment.lines.first()
    line_without_reason = fulfillment.lines.last()
    line_reason = "Damaged"

    variables = {
        "order": order_id,
        "input": {
            "refund": False,
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": to_global_id_or_none(line_with_reason),
                    "quantity": 1,
                    "replace": False,
                    "reason": line_reason,
                    "reasonReference": to_global_id_or_none(line_page),
                },
                {
                    "fulfillmentLineId": to_global_id_or_none(line_without_reason),
                    "quantity": 1,
                    "replace": False,
                },
            ],
            "reasonReference": to_global_id_or_none(global_page),
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
    return_fulfillment = order.fulfillments.get(status=FulfillmentStatus.RETURNED)
    assert return_fulfillment.reason_reference == global_page

    lines_by_order_line = {
        line.order_line_id: line for line in return_fulfillment.lines.all()
    }
    assert (
        lines_by_order_line[line_with_reason.order_line_id].reason_reference
        == line_page
    )
    assert (
        lines_by_order_line[line_without_reason.order_line_id].reason_reference is None
    )


def test_fulfillment_return_products_refund_requires_reason_reference_for_staff(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
    site_settings,
):
    # given - refund=true uses the same validation as refund=false: staff must
    # provide the global reasonReference when the type is configured
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)

    order = fulfilled_order
    order_id = graphene.Node.to_global_id("Order", order.pk)
    fulfillment_line = order.fulfillments.first().lines.first()

    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": to_global_id_or_none(fulfillment_line),
                    "quantity": 1,
                    "replace": False,
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
    assert errors[0]["code"] == OrderErrorCode.REQUIRED.name
    assert not order.fulfillments.filter(
        status__in=[
            FulfillmentStatus.RETURNED,
            FulfillmentStatus.REFUNDED_AND_RETURNED,
        ]
    ).exists()


@patch("saleor.payment.gateway.refund")
def test_fulfillment_return_products_refund_stores_reason_reference(
    mocked_refund,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
    site_settings,
):
    # given - refund=true with a valid global reasonReference stores the reference
    # on the resulting fulfillment, same as refund=false
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    page = Page.objects.create(
        slug="customer-return",
        title="Customer return",
        page_type=page_type,
        is_published=True,
    )
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)

    order = fulfilled_order
    order_id = graphene.Node.to_global_id("Order", order.pk)
    fulfillment_line = order.fulfillments.first().lines.first()
    global_reason = "Customer return request"

    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": to_global_id_or_none(fulfillment_line),
                    "quantity": 1,
                    "replace": False,
                },
            ],
            "reason": global_reason,
            "reasonReference": to_global_id_or_none(page),
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    assert not data["errors"]
    mocked_refund.assert_called_once()

    order.refresh_from_db()
    return_fulfillment = order.fulfillments.get(
        status=FulfillmentStatus.REFUNDED_AND_RETURNED
    )
    assert return_fulfillment.reason == global_reason
    assert return_fulfillment.reason_reference == page


def test_fulfillment_return_products_replace_with_per_line_reasons(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    site_settings,
):
    # given - one line is replaced and one is returned, each with its own
    # per-line reasonReference (refund disabled)
    page_type = PageType.objects.create(name="Return Reasons", slug="return-reasons")
    replace_page = Page.objects.create(
        slug="damaged", title="Damaged", page_type=page_type, is_published=True
    )
    return_page = Page.objects.create(
        slug="wrong-size", title="Wrong size", page_type=page_type, is_published=True
    )
    global_page = Page.objects.create(
        slug="customer-return",
        title="Customer return",
        page_type=page_type,
        is_published=True,
    )
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = fulfilled_order
    order_id = graphene.Node.to_global_id("Order", order.pk)
    fulfillment = order.fulfillments.first()
    line_to_replace = fulfillment.lines.first()
    line_to_return = fulfillment.lines.last()

    variables = {
        "order": order_id,
        "input": {
            "refund": False,
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": to_global_id_or_none(line_to_replace),
                    "quantity": 1,
                    "replace": True,
                    "reason": "Damaged",
                    "reasonReference": to_global_id_or_none(replace_page),
                },
                {
                    "fulfillmentLineId": to_global_id_or_none(line_to_return),
                    "quantity": 1,
                    "replace": False,
                    "reason": "Wrong size",
                    "reasonReference": to_global_id_or_none(return_page),
                },
            ],
            "reasonReference": to_global_id_or_none(global_page),
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    assert not data["errors"]
    assert data["replaceFulfillment"]["status"] == FulfillmentStatus.REPLACED.upper()
    assert data["returnFulfillment"]["status"] == FulfillmentStatus.RETURNED.upper()
    assert data["replaceOrder"]

    order.refresh_from_db()
    replace_fulfillment = order.fulfillments.get(status=FulfillmentStatus.REPLACED)
    assert replace_fulfillment.reason_reference == global_page
    replaced_line = replace_fulfillment.lines.get(
        order_line_id=line_to_replace.order_line_id
    )
    assert replaced_line.reason_reference == replace_page

    return_fulfillment = order.fulfillments.get(status=FulfillmentStatus.RETURNED)
    assert return_fulfillment.reason_reference == global_page
    returned_line = return_fulfillment.lines.get(
        order_line_id=line_to_return.order_line_id
    )
    assert returned_line.reason_reference == return_page
