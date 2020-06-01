from unittest.mock import patch

import graphene

from saleor.core import JobStatus
from saleor.graphql.invoice.enums import PendingTarget
from saleor.invoice.error_codes import InvoiceErrorCode
from saleor.invoice.models import Invoice, InvoiceEvent, InvoiceEvents
from saleor.order import OrderStatus

from .utils import assert_no_permission, get_graphql_content

REQUEST_INVOICE_MUTATION = """
    mutation RequestInvoice($orderId: ID!, $number: String) {
        requestInvoice(
            orderId: $orderId
            number: $number
        ) {
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


CREATE_INVOICE_MUTATION = """
    mutation CreateInvoice($orderId: ID!, $number: String!, $url: String!) {
        createInvoice(
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
            invoiceErrors {
                field
                code
            }
        }
    }
"""


REQUEST_DELETE_INVOICE_MUTATION = """
    mutation RequestDeleteInvoice($id: ID!) {
        requestDeleteInvoice(
            id: $id
        ) {
            invoiceErrors {
                field
                code
            }
        }
    }
"""


DELETE_INVOICE_MUTATION = """
    mutation DeleteInvoice($id: ID!) {
        deleteInvoice(
            id: $id
        ) {
            invoiceErrors {
                field
                code
            }
        }
    }
"""


UPDATE_INVOICE_MUTATION = """
    mutation UpdateInvoice($id: ID!, $number: String, $url: String) {
        updateInvoice(
            id: $id
            input: {
                number: $number
                url: $url
            }
        ) {
            invoice {
                number
                url
                metadata {
                    key
                    value
                }
            }
            invoiceErrors {
                field
                code
            }
        }
    }
"""


SEND_INVOICE_MUTATION = """
    mutation SendInvoice($id: ID!) {
        sendInvoiceEmail(
            id: $id
        ) {
            invoiceErrors {
                field
                code
            }
        }
    }
"""


@patch("saleor.plugins.base_plugin.BasePlugin.invoice_request")
def test_request_invoice(
    plugin_mock, staff_api_client, permission_manage_orders, order
):
    number = "01/12/2020/TEST"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
    }
    response = staff_api_client.post_graphql(
        REQUEST_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
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
        content["data"]["requestInvoice"]["invoice"]["status"]
        == JobStatus.PENDING.upper()
    )
    assert invoice.pending_target == PendingTarget.COMPLETE


def test_request_invoice_draft_order(staff_api_client, permission_manage_orders, order):
    order.status = OrderStatus.DRAFT
    order.save()
    number = "01/12/2020/TEST"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
    }
    response = staff_api_client.post_graphql(
        REQUEST_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(number=number, order=order.pk).exists()
    error = content["data"]["requestInvoice"]["invoiceErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.INVALID_STATUS.name


def test_request_invoice_no_billing_address(
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
        REQUEST_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(number=number, order=order.pk).exists()
    error = content["data"]["requestInvoice"]["invoiceErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.NOT_READY.name


def test_request_invoice_no_number(staff_api_client, permission_manage_orders, order):
    variables = {"orderId": graphene.Node.to_global_id("Order", order.pk)}
    staff_api_client.post_graphql(
        REQUEST_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    invoice = Invoice.objects.get(order=order.pk)
    assert invoice.number is None


def test_request_invoice_invalid_order(staff_api_client, permission_manage_orders):
    variables = {"orderId": "T3JkZXI6MTMzNzEzMzc=", "number": "01/12/2020/TEST"}
    response = staff_api_client.post_graphql(
        REQUEST_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["requestInvoice"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "orderId"


@patch("saleor.plugins.base_plugin.BasePlugin.invoice_delete")
def test_request_delete_invoice(
    plugin_mock, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(order=order)
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(REQUEST_DELETE_INVOICE_MUTATION, variables)
    invoice.refresh_from_db()
    assert invoice.pending_target == PendingTarget.DELETE
    plugin_mock.assert_called_once_with(invoice, previous_value=None)
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.REQUESTED_DELETION,
        user=staff_api_client.user,
        invoice=invoice,
        order=invoice.order,
    ).exists()


@patch("saleor.plugins.base_plugin.BasePlugin.invoice_delete")
def test_request_delete_invoice_invalid_id(
    plugin_mock, staff_api_client, permission_manage_orders
):
    variables = {"id": graphene.Node.to_global_id("Invoice", 1337)}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(REQUEST_DELETE_INVOICE_MUTATION, variables)
    content = get_graphql_content(response)
    error = content["data"]["requestDeleteInvoice"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "id"
    plugin_mock.assert_not_called()


@patch("saleor.plugins.base_plugin.BasePlugin.invoice_delete")
def test_request_delete_invoice_no_permission(
    plugin_mock, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(order=order)
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(REQUEST_DELETE_INVOICE_MUTATION, variables)
    assert_no_permission(response)
    plugin_mock.assert_not_called()


def test_delete_invoice(staff_api_client, permission_manage_orders, order):
    invoice = Invoice.objects.create(order=order)
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        DELETE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["deleteInvoice"]["invoiceErrors"]
    assert not Invoice.objects.filter(id=invoice.pk).exists()
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.DELETED,
        user=staff_api_client.user,
        parameters__invoice_id=invoice.id,
    ).exists()


@patch("saleor.plugins.base_plugin.BasePlugin.invoice_delete")
def test_delete_invoice_invalid_id(
    plugin_mock, staff_api_client, permission_manage_orders
):
    variables = {"id": graphene.Node.to_global_id("Invoice", 1337)}
    response = staff_api_client.post_graphql(
        DELETE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["deleteInvoice"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "id"
    plugin_mock.assert_not_called()


def test_update_invoice(staff_api_client, permission_manage_orders, order):
    test_key = "test_key"
    metadata = {test_key: "test_val"}
    invoice = Invoice.objects.create(order=order, metadata=metadata)
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("Invoice", invoice.pk),
        "number": number,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        UPDATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    assert invoice.status == JobStatus.SUCCESS
    assert invoice.number == content["data"]["updateInvoice"]["invoice"]["number"]
    response_metadata = content["data"]["updateInvoice"]["invoice"]["metadata"][0]
    assert response_metadata["key"] == test_key
    assert response_metadata["value"] == metadata[test_key]
    assert invoice.url == content["data"]["updateInvoice"]["invoice"]["url"]


def test_update_invoice_single_value(staff_api_client, permission_manage_orders, order):
    number = "01/12/2020/TEST"
    invoice = Invoice.objects.create(order=order, number=number)
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("Invoice", invoice.pk),
        "url": url,
    }
    response = staff_api_client.post_graphql(
        UPDATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    assert invoice.status == JobStatus.SUCCESS
    assert invoice.number == number
    assert invoice.url == content["data"]["updateInvoice"]["invoice"]["url"]


def test_update_invoice_missing_number(
    staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(order=order)
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("Invoice", invoice.pk),
        "url": url,
    }
    response = staff_api_client.post_graphql(
        UPDATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    error = content["data"]["updateInvoice"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.URL_OR_NUMBER_NOT_SET.name
    assert error["field"] == "invoice"
    assert invoice.url is None
    assert invoice.status == JobStatus.PENDING


def test_update_invoice_invalid_id(staff_api_client, permission_manage_orders):
    variables = {"id": "SW52b2ljZToxMzM3", "number": "01/12/2020/TEST"}
    response = staff_api_client.post_graphql(
        UPDATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["updateInvoice"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "id"


def test_create_invoice(staff_api_client, permission_manage_orders, order):
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        CREATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice = Invoice.objects.get(order=order, status=JobStatus.SUCCESS)
    assert invoice.url == content["data"]["createInvoice"]["invoice"]["url"]
    assert invoice.number == content["data"]["createInvoice"]["invoice"]["number"]
    assert (
        invoice.status.upper() == content["data"]["createInvoice"]["invoice"]["status"]
    )
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.CREATED,
        user=staff_api_client.user,
        invoice=invoice,
        order=invoice.order,
        parameters__number=number,
        parameters__url=url,
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
        CREATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(order_id=order.pk, number=number).exists()
    error = content["data"]["createInvoice"]["invoiceErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.NOT_READY.name


def test_create_invoice_for_draft_order(
    staff_api_client, permission_manage_orders, order
):
    order.status = OrderStatus.DRAFT
    order.save()
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        CREATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(order_id=order.pk, number=number).exists()
    error = content["data"]["createInvoice"]["invoiceErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.INVALID_STATUS.name


def test_create_invoice_invalid_id(staff_api_client, permission_manage_orders):
    variables = {
        "orderId": graphene.Node.to_global_id("Order", 1337),
        "number": "01/12/2020/TEST",
        "url": "http://www.example.com",
    }
    response = staff_api_client.post_graphql(
        CREATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["createInvoice"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "orderId"


def test_create_invoice_empty_params(staff_api_client, permission_manage_orders, order):
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": "",
        "url": "",
    }
    response = staff_api_client.post_graphql(
        CREATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["createInvoice"]["invoiceErrors"]
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


@patch("saleor.invoice.emails.send_invoice.delay")
def test_send_invoice(email_mock, staff_api_client, permission_manage_orders, order):
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    invoice = Invoice.objects.create(
        order=order, number=number, url=url, status=JobStatus.SUCCESS
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        SEND_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["sendInvoiceEmail"]["invoiceErrors"]
    email_mock.assert_called_with(invoice.pk)
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.SENT,
        user=staff_api_client.user,
        invoice=invoice,
        parameters__email=order.user.email,
    ).exists()


@patch("saleor.invoice.emails.send_invoice.delay")
def test_send_pending_invoice(
    email_mock, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(
        order=order, number=None, url=None, status=JobStatus.PENDING
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        SEND_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["sendInvoiceEmail"]["invoiceErrors"]
    assert errors == [{"field": None, "code": InvoiceErrorCode.NOT_READY.name}]
    email_mock.assert_not_called()


@patch("saleor.invoice.emails.send_invoice.delay")
def test_send_not_ready_invoice(
    email_mock, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(
        order=order, number=None, url=None, status=JobStatus.SUCCESS
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        SEND_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["sendInvoiceEmail"]["invoiceErrors"]
    [{"field": None, "code": "URL_OR_NUMBER_NOT_SET"}]
    assert errors == [
        {"field": None, "code": InvoiceErrorCode.URL_OR_NUMBER_NOT_SET.name}
    ]
    email_mock.assert_not_called()
