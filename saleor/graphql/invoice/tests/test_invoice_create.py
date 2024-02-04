import uuid

import graphene
import pytest

from ....core import JobStatus
from ....graphql.tests.utils import assert_no_permission, get_graphql_content
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.models import Invoice, InvoiceEvent, InvoiceEvents
from ....order import OrderEvents, OrderStatus

INVOICE_CREATE_MUTATION = """
    mutation InvoiceCreate($orderId: ID!, $input: InvoiceCreateInput!) {
        invoiceCreate(
            orderId: $orderId,
            input: $input
        ) {
            invoice {
                status
                number
                url
                order {
                    id
                }
                metadata {
                    key
                    value
                }
                privateMetadata {
                    key
                    value
                }
            }
            errors {
                field
                code
            }
        }
    }
"""


def test_create_invoice(staff_api_client, permission_group_manage_orders, order):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    order_id = graphene.Node.to_global_id("Order", order.pk)
    metadata = [{"key": "test key", "value": "test value"}]
    private_metadata = [{"key": "private test key", "value": "private test value"}]
    variables = {
        "orderId": order_id,
        "input": {
            "number": number,
            "url": url,
            "metadata": metadata,
            "privateMetadata": private_metadata,
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    invoice = Invoice.objects.get(order=order, status=JobStatus.SUCCESS)
    assert order_id == content["data"]["invoiceCreate"]["invoice"]["order"]["id"]
    assert content["data"]["invoiceCreate"]["invoice"]["metadata"] == metadata
    assert (
        content["data"]["invoiceCreate"]["invoice"]["privateMetadata"]
        == private_metadata
    )
    assert invoice.url == content["data"]["invoiceCreate"]["invoice"]["url"]
    assert invoice.number == content["data"]["invoiceCreate"]["invoice"]["number"]
    assert (
        invoice.status.upper() == content["data"]["invoiceCreate"]["invoice"]["status"]
    )
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.CREATED,
        user=staff_api_client.user,
        invoice=invoice,
        order=invoice.order,
        parameters__number=number,
        parameters__url=url,
    ).exists()
    assert order.events.filter(
        type=OrderEvents.INVOICE_GENERATED,
        order=order,
        user=staff_api_client.user,
        parameters__invoice_number=number,
    ).exists()


def test_create_invoice_by_user_no_channel_access(
    staff_api_client, permission_group_all_perms_channel_USD_only, order, channel_PLN
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    number = "01/12/2020/TEST"
    url = "http://www.example.com"

    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {
        "orderId": order_id,
        "input": {
            "number": number,
            "url": url,
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_create_invoice_by_app(app_api_client, permission_manage_orders, order):
    # given
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {
        "orderId": order_id,
        "input": {
            "number": number,
            "url": url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        INVOICE_CREATE_MUTATION, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    invoice = Invoice.objects.get(order=order, status=JobStatus.SUCCESS)
    assert order_id == content["data"]["invoiceCreate"]["invoice"]["order"]["id"]
    assert invoice.url == content["data"]["invoiceCreate"]["invoice"]["url"]
    assert invoice.number == content["data"]["invoiceCreate"]["invoice"]["number"]
    assert (
        invoice.status.upper() == content["data"]["invoiceCreate"]["invoice"]["status"]
    )
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.CREATED,
        user=None,
        app=app_api_client.app,
        invoice=invoice,
        order=invoice.order,
        parameters__number=number,
        parameters__url=url,
    ).exists()
    assert order.events.filter(
        type=OrderEvents.INVOICE_GENERATED,
        order=order,
        user=None,
        app=app_api_client.app,
        parameters__invoice_number=number,
    ).exists()


def test_create_invoice_no_billing_address(
    staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order.billing_address = None
    order.save()
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {
            "number": number,
            "url": url,
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(order_id=order.pk, number=number).exists()
    error = content["data"]["invoiceCreate"]["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.NOT_READY.name
    assert not order.events.filter(type=OrderEvents.INVOICE_GENERATED).exists()


@pytest.mark.parametrize(
    "status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED, OrderStatus.EXPIRED]
)
def test_create_invoice_invalid_order_status(
    status, staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order.status = status
    order.save()
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {
            "number": number,
            "url": url,
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(order_id=order.pk, number=number).exists()
    error = content["data"]["invoiceCreate"]["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.INVALID_STATUS.name
    assert not order.events.filter(type=OrderEvents.INVOICE_GENERATED).exists()


def test_create_invoice_invalid_id(staff_api_client, permission_group_manage_orders):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "orderId": graphene.Node.to_global_id("Order", uuid.uuid4()),
        "input": {
            "number": "01/12/2020/TEST",
            "url": "http://www.example.com",
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["invoiceCreate"]["errors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "orderId"


def test_create_invoice_empty_params(
    staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {
            "number": "",
            "url": "",
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["invoiceCreate"]["errors"]
    assert errors[0] == {
        "field": "url",
        "code": InvoiceErrorCode.REQUIRED.name,
    }
    assert errors[1] == {
        "field": "number",
        "code": InvoiceErrorCode.REQUIRED.name,
    }

    assert not Invoice.objects.filter(
        order__id=order.pk, status=JobStatus.SUCCESS
    ).exists()
    assert not order.events.filter(type=OrderEvents.INVOICE_GENERATED).exists()
