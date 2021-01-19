from unittest.mock import patch

import graphene
import pytest

from ....core import JobStatus
from ....graphql.tests.utils import get_graphql_content
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.models import Invoice, InvoiceEvent, InvoiceEvents
from ....order import OrderEvents, OrderStatus
from ....order.models import OrderEvent

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


@pytest.fixture(autouse=True)
def setup_dummy_gateways(settings):
    settings.PLUGINS = [
        "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin",
    ]
    return settings


@patch("saleor.plugins.base_plugin.BasePlugin.invoice_request")
def test_invoice_request(
    plugin_mock, staff_api_client, permission_manage_orders, order
):
    dummy_invoice = Invoice.objects.create(order=order)
    plugin_mock.return_value = dummy_invoice
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
    assert invoice.order.events.filter(
        type=OrderEvents.INVOICE_REQUESTED, order=order, user=staff_api_client.user
    ).exists()


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_invoice_request_invalid_order_status(
    status, staff_api_client, permission_manage_orders, order
):
    order.status = status
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
    assert not OrderEvent.objects.filter(type=OrderEvents.INVOICE_REQUESTED).exists()


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
    assert not OrderEvent.objects.filter(type=OrderEvents.INVOICE_REQUESTED).exists()


def test_invoice_request_no_number(staff_api_client, permission_manage_orders, order):
    variables = {"orderId": graphene.Node.to_global_id("Order", order.pk)}
    staff_api_client.post_graphql(
        INVOICE_REQUEST_MUTATION, variables, permissions=[permission_manage_orders]
    )
    invoice = Invoice.objects.get(order=order.pk)
    assert invoice.number is None
    assert not OrderEvent.objects.filter(type=OrderEvents.INVOICE_REQUESTED).exists()


def test_invoice_request_invalid_id(staff_api_client, permission_manage_orders):
    variables = {"orderId": "T3JkZXI6MTMzNzEzMzc=", "number": "01/12/2020/TEST"}
    response = staff_api_client.post_graphql(
        INVOICE_REQUEST_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["invoiceRequest"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "orderId"
