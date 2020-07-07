from unittest.mock import patch

import graphene

from ....core import JobStatus
from ....graphql.tests.utils import get_graphql_content
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.models import Invoice, InvoiceEvent, InvoiceEvents
from ....order import OrderStatus

INVOICE_REQUEST_MUTATION = """
    mutation InvoiceRequest($orderId: ID!, $number: String) {
        invoiceRequest(
            orderId: $orderId
            number: $number
        ) {
            order {
                id
            }
            invoice {
                status
                number
                url
            }
            invoiceErrors {
                field
                code
            }
        }
    }
"""


@patch("saleor.plugins.base_plugin.BasePlugin.invoice_request")
def test_invoice_request(
    plugin_mock, staff_api_client, permission_manage_orders, order
):
    number = "01/12/2020/TEST"
    graphene_order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {
        "orderId": graphene_order_id,
        "number": number,
    }
    response = staff_api_client.post_graphql(
        INVOICE_REQUEST_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice = Invoice.objects.filter(
        number=number, order=order.pk, status=JobStatus.PENDING
    ).first()
    assert invoice
    plugin_mock.assert_called_once_with(order, invoice, number, previous_value=None)
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.REQUESTED,
        user=staff_api_client.user,
        order=invoice.order,
        parameters__number=number,
    ).exists()
    assert (
        content["data"]["invoiceRequest"]["invoice"]["status"]
        == JobStatus.PENDING.upper()
    )
    assert content["data"]["invoiceRequest"]["order"]["id"] == graphene_order_id


def test_invoice_request_draft_order(staff_api_client, permission_manage_orders, order):
    order.status = OrderStatus.DRAFT
    order.save()
    number = "01/12/2020/TEST"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
    }
    response = staff_api_client.post_graphql(
        INVOICE_REQUEST_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(number=number, order=order.pk).exists()
    error = content["data"]["invoiceRequest"]["invoiceErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.INVALID_STATUS.name


def test_invoice_request_no_billing_address(
    staff_api_client, permission_manage_orders, order
):
    order.billing_address = None
    order.save()
    number = "01/12/2020/TEST"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
    }
    response = staff_api_client.post_graphql(
        INVOICE_REQUEST_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(number=number, order=order.pk).exists()
    error = content["data"]["invoiceRequest"]["invoiceErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.NOT_READY.name


def test_invoice_request_no_number(staff_api_client, permission_manage_orders, order):
    variables = {"orderId": graphene.Node.to_global_id("Order", order.pk)}
    staff_api_client.post_graphql(
        INVOICE_REQUEST_MUTATION, variables, permissions=[permission_manage_orders]
    )
    invoice = Invoice.objects.get(order=order.pk)
    assert invoice.number is None


def test_invoice_request_invalid_order(staff_api_client, permission_manage_orders):
    variables = {"orderId": "T3JkZXI6MTMzNzEzMzc=", "number": "01/12/2020/TEST"}
    response = staff_api_client.post_graphql(
        INVOICE_REQUEST_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["invoiceRequest"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "orderId"
