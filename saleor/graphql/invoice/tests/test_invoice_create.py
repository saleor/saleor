import uuid

import graphene
import pytest

from ....core import JobStatus
from ....graphql.tests.utils import get_graphql_content
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.models import Invoice, InvoiceEvent, InvoiceEvents
from ....order import OrderEvents, OrderStatus

INVOICE_CREATE_MUTATION = """
    mutation InvoiceCreate($orderId: ID!, $number: String!, $url: String!) {
        invoiceCreate(
            orderId: $orderId,
            input: {
                number: $number,
                url: $url
            }
        ) {
            invoice {
                status
                number
                url
            }
            errors {
                field
                code
            }
        }
    }
"""


def test_create_invoice(staff_api_client, permission_manage_orders, order):
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        INVOICE_CREATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice = Invoice.objects.get(order=order, status=JobStatus.SUCCESS)
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


def test_create_invoice_no_billing_address(
    staff_api_client, permission_manage_orders, order
):
    order.billing_address = None
    order.save()
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        INVOICE_CREATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(order_id=order.pk, number=number).exists()
    error = content["data"]["invoiceCreate"]["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.NOT_READY.name
    assert not order.events.filter(type=OrderEvents.INVOICE_GENERATED).exists()


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
def test_create_invoice_invalid_order_status(
    status, staff_api_client, permission_manage_orders, order
):
    order.status = status
    order.save()
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        INVOICE_CREATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(order_id=order.pk, number=number).exists()
    error = content["data"]["invoiceCreate"]["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.INVALID_STATUS.name
    assert not order.events.filter(type=OrderEvents.INVOICE_GENERATED).exists()


def test_create_invoice_invalid_id(staff_api_client, permission_manage_orders):
    variables = {
        "orderId": graphene.Node.to_global_id("Order", uuid.uuid4()),
        "number": "01/12/2020/TEST",
        "url": "http://www.example.com",
    }
    response = staff_api_client.post_graphql(
        INVOICE_CREATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["invoiceCreate"]["errors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "orderId"


def test_create_invoice_empty_params(staff_api_client, permission_manage_orders, order):
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": "",
        "url": "",
    }
    response = staff_api_client.post_graphql(
        INVOICE_CREATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
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
