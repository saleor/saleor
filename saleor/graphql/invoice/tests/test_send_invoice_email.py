from unittest.mock import patch

import graphene

from ....core import JobStatus
from ....graphql.tests.utils import get_graphql_content
from ....invoice.emails import collect_invoice_data_for_email
from ....invoice.models import Invoice, InvoiceEvent, InvoiceEvents
from ....order import OrderEvents

INVOICE_SEND_EMAIL_MUTATION = """
    mutation invoiceSendEmail($id: ID!) {
        invoiceSendEmail(
            id: $id
        ) {
            invoiceErrors {
                field
                code
            }
        }
    }
"""


@patch("saleor.invoice.emails.send_templated_mail")
def test_invoice_send_email(
    email_mock, staff_api_client, permission_manage_orders, order
):
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    invoice = Invoice.objects.create(
        order=order, number=number, url=url, status=JobStatus.SUCCESS
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        INVOICE_SEND_EMAIL_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    call_args = collect_invoice_data_for_email(invoice, "order/send_invoice")
    email_mock.assert_called_once_with(**call_args)
    assert not content["data"]["invoiceSendEmail"]["invoiceErrors"]
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.SENT,
        user=staff_api_client.user,
        invoice=invoice,
        parameters__email=order.user.email,
    ).exists()
    assert order.events.filter(
        type=OrderEvents.INVOICE_SENT,
        order=order,
        user=staff_api_client.user,
        parameters__email=order.user.email,
    ).exists()


@patch("saleor.invoice.emails.send_templated_mail")
def test_invoice_send_email_pending(
    email_mock, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(
        order=order, number=None, url=None, status=JobStatus.PENDING
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        INVOICE_SEND_EMAIL_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["invoiceSendEmail"]["invoiceErrors"]
    assert errors == [
        {"field": "invoice", "code": "NOT_READY"},
        {"field": "url", "code": "URL_NOT_SET"},
        {"field": "number", "code": "NUMBER_NOT_SET"},
    ]
    email_mock.assert_not_called()
    assert not order.events.filter(type=OrderEvents.INVOICE_SENT).exists()


@patch("saleor.invoice.emails.send_templated_mail")
def test_invoice_send_email_without_url_and_number(
    email_mock, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(
        order=order, number=None, url=None, status=JobStatus.SUCCESS
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        INVOICE_SEND_EMAIL_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["invoiceSendEmail"]["invoiceErrors"]
    assert errors == [
        {"field": "url", "code": "URL_NOT_SET"},
        {"field": "number", "code": "NUMBER_NOT_SET"},
    ]
    email_mock.assert_not_called()
    assert not order.events.filter(type=OrderEvents.INVOICE_SENT).exists()


@patch("saleor.invoice.emails.send_templated_mail")
@patch("saleor.order.models.Order.get_customer_email")
def test_invoice_send_email_without_email(
    order_mock, email_mock, staff_api_client, permission_manage_orders, order
):
    order_mock.return_value = None
    invoice = Invoice.objects.create(
        order=order,
        number="01/12/2020/TEST",
        url="http://www.example.com",
        status=JobStatus.SUCCESS,
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        INVOICE_SEND_EMAIL_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    email_mock.assert_not_called()
    assert order_mock.called
    errors = content["data"]["invoiceSendEmail"]["invoiceErrors"]
    assert errors == [{"field": "order", "code": "EMAIL_NOT_SET"}]
    assert not order.events.filter(type=OrderEvents.INVOICE_SENT).exists()
