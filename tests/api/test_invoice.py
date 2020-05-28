import uuid
from unittest.mock import Mock, patch

import graphene

from saleor.graphql.invoice.enums import InvoiceStatus
from saleor.invoice.error_codes import InvoiceErrorCode
from saleor.invoice.models import Invoice, InvoiceEvent, InvoiceEvents, InvoiceJob
from saleor.order import OrderStatus

from .utils import assert_no_permission, get_graphql_content

REQUEST_INVOICE_MUTATION = """
    mutation RequestInvoice($orderId: ID!, $number: String) {
        requestInvoice(
            orderId: $orderId,
            number: $number
        ) {
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
            invoiceJob {
                status,
                invoice {
                    number
                    url
                }
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
            id: $id,
            input: {
                number: $number,
                url: $url
            }
        ) {
            invoiceJob {
                invoice {
                    number
                    url
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
    staff_api_client.post_graphql(
        REQUEST_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    invoice = Invoice.objects.filter(number=number, order=order.pk).first()
    invoice_job = InvoiceJob.objects.get(
        invoice__id=invoice.pk, status=InvoiceStatus.PENDING
    )
    assert invoice
    assert invoice_job
    plugin_mock.assert_called_once_with(order, invoice_job, number, previous_value=None)
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.REQUESTED,
        user=staff_api_client.user,
        order=invoice.order,
        parameters__number=number,
    ).exists()


@patch("saleor.plugins.invoicing.default_storage")
def test_request_invoice_with_plugin(
    stor_mock, staff_api_client, permission_manage_orders, order, setup_invoicing
):
    stor_mock.save = Mock(return_value=f"{uuid.uuid4()}.pdf")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
    }
    staff_api_client.post_graphql(
        REQUEST_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    job = InvoiceJob.objects.get(invoice__order=order)
    assert job.status == InvoiceStatus.READY


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
    invoice_job = InvoiceJob.objects.create(invoice=invoice)
    variables = {"id": graphene.Node.to_global_id("InvoiceJob", invoice_job.pk)}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(REQUEST_DELETE_INVOICE_MUTATION, variables)
    invoice.refresh_from_db()
    assert InvoiceJob.objects.filter(
        invoice__id=invoice.pk, status=InvoiceStatus.PENDING_DELETE
    ).exists()
    plugin_mock.assert_called_once_with(invoice_job, previous_value=None)
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
    variables = {"id": graphene.Node.to_global_id("InvoiceJob", 1337)}
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
    invoice_job = InvoiceJob.objects.create(invoice=invoice)
    variables = {"id": graphene.Node.to_global_id("InvoiceJob", invoice_job.pk)}
    response = staff_api_client.post_graphql(
        DELETE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["deleteInvoice"]["invoiceErrors"]
    assert not InvoiceJob.objects.filter(invoice__id=invoice.pk).exists()
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.DELETED,
        user=staff_api_client.user,
        parameters__invoice_id=invoice.id,
    ).exists()


@patch("saleor.plugins.base_plugin.BasePlugin.invoice_delete")
def test_delete_invoice_invalid_id(
    plugin_mock, staff_api_client, permission_manage_orders
):
    variables = {"id": graphene.Node.to_global_id("InvoiceJob", 1337)}
    response = staff_api_client.post_graphql(
        DELETE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["deleteInvoice"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "id"
    plugin_mock.assert_not_called()


def test_update_invoice(staff_api_client, permission_manage_orders, order):
    invoice = Invoice.objects.create(order=order)
    invoice_job = InvoiceJob.objects.create(invoice=invoice)
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("InvoiceJob", invoice_job.pk),
        "number": number,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        UPDATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    invoice_job.refresh_from_db()
    assert invoice_job.status == InvoiceStatus.READY
    assert (
        invoice.number
        == content["data"]["updateInvoice"]["invoiceJob"]["invoice"]["number"]
    )
    assert (
        invoice.url == content["data"]["updateInvoice"]["invoiceJob"]["invoice"]["url"]
    )


def test_update_invoice_single_value(staff_api_client, permission_manage_orders, order):
    number = "01/12/2020/TEST"
    invoice = Invoice.objects.create(order=order, number=number)
    invoice_job = InvoiceJob.objects.create(invoice=invoice)
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("InvoiceJob", invoice_job.pk),
        "url": url,
    }
    response = staff_api_client.post_graphql(
        UPDATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    invoice_job.refresh_from_db()
    assert invoice_job.status == InvoiceStatus.READY
    assert invoice.number == number
    assert (
        invoice.url == content["data"]["updateInvoice"]["invoiceJob"]["invoice"]["url"]
    )


def test_update_invoice_missing_number(
    staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(order=order)
    invoice_job = InvoiceJob.objects.create(invoice=invoice)
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("InvoiceJob", invoice_job.pk),
        "url": url,
    }
    response = staff_api_client.post_graphql(
        UPDATE_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    invoice_job.refresh_from_db()
    error = content["data"]["updateInvoice"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.URL_OR_NUMBER_NOT_SET.name
    assert error["field"] == "invoice"
    assert invoice.url is None
    assert invoice_job.status == InvoiceStatus.PENDING


def test_update_invoice_invalid_id(staff_api_client, permission_manage_orders):
    variables = {"id": "SW52b2ljZUpvYjoxMzM3", "number": "01/12/2020/TEST"}
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
    job = InvoiceJob.objects.get(
        invoice__order__id=order.pk, status=InvoiceStatus.READY
    )
    assert (
        job.invoice.url
        == content["data"]["createInvoice"]["invoiceJob"]["invoice"]["url"]
    )
    assert (
        job.invoice.number
        == content["data"]["createInvoice"]["invoiceJob"]["invoice"]["number"]
    )
    assert (
        job.status.upper() == content["data"]["createInvoice"]["invoiceJob"]["status"]
    )
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.CREATED,
        user=staff_api_client.user,
        invoice=job.invoice,
        order=job.invoice.order,
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
    assert not Invoice.objects.filter(
        order_id=order.pk, url=url, number=number
    ).exists()
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
    assert not Invoice.objects.filter(
        order_id=order.pk, url=url, number=number
    ).exists()
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

    assert not InvoiceJob.objects.filter(
        invoice__order__id=order.pk, status=InvoiceStatus.READY
    ).exists()


@patch("saleor.invoice.emails.send_invoice.delay")
def test_send_invoice(email_mock, staff_api_client, permission_manage_orders, order):
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    invoice = Invoice.objects.create(order=order, number=number, url=url)
    invoice_job = InvoiceJob.objects.create(invoice=invoice, status=InvoiceStatus.READY)
    variables = {"id": graphene.Node.to_global_id("InvoiceJob", invoice_job.pk)}
    response = staff_api_client.post_graphql(
        SEND_INVOICE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["sendInvoiceEmail"]["invoiceErrors"]
    email_mock.assert_called_with(invoice_job.pk)
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
    invoice = Invoice.objects.create(order=order, number=None, url=None)
    invoice_job = InvoiceJob.objects.create(
        invoice=invoice, status=InvoiceStatus.PENDING
    )
    variables = {"id": graphene.Node.to_global_id("InvoiceJob", invoice_job.pk)}
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
    invoice = Invoice.objects.create(order=order, number=None, url=None)
    invoice_job = InvoiceJob.objects.create(invoice=invoice, status=InvoiceStatus.READY)
    variables = {"id": graphene.Node.to_global_id("InvoiceJob", invoice_job.pk)}
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
