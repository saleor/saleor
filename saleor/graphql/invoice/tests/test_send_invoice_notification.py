from unittest.mock import patch

import graphene

from ....core import JobStatus
from ....core.notify_events import NotifyEventType
from ....graphql.tests.utils import get_graphql_content
from ....invoice.models import Invoice, InvoiceEvent, InvoiceEvents
from ....invoice.notifications import get_invoice_payload
from ....order import OrderEvents

INVOICE_SEND_EMAIL_MUTATION = """
    mutation invoiceSendNotification($id: ID!) {
        invoiceSendNotification(
            id: $id
        ) {
            invoiceErrors {
                field
                code
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_invoice_send_notification(
    mock_notify, staff_api_client, permission_manage_orders, order
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
    expected_payload = get_invoice_payload(invoice)

    mock_notify.assert_called_once_with(NotifyEventType.INVOICE_READY, expected_payload)
    assert not content["data"]["invoiceSendNotification"]["invoiceErrors"]
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


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_invoice_send_notification_pending(
    mock_notify, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(
        order=order, number=None, url=None, status=JobStatus.PENDING
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        INVOICE_SEND_EMAIL_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["invoiceSendNotification"]["invoiceErrors"]
    assert errors == [
        {"field": "invoice", "code": "NOT_READY"},
        {"field": "url", "code": "URL_NOT_SET"},
        {"field": "number", "code": "NUMBER_NOT_SET"},
    ]
    mock_notify.assert_not_called()
    assert not order.events.filter(type=OrderEvents.INVOICE_SENT).exists()


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_invoice_send_notification_without_url_and_number(
    mock_notify, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(
        order=order, number=None, url=None, status=JobStatus.SUCCESS
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        INVOICE_SEND_EMAIL_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["invoiceSendNotification"]["invoiceErrors"]
    assert errors == [
        {"field": "url", "code": "URL_NOT_SET"},
        {"field": "number", "code": "NUMBER_NOT_SET"},
    ]
    mock_notify.assert_not_called()
    assert not order.events.filter(type=OrderEvents.INVOICE_SENT).exists()


@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.order.models.Order.get_customer_email")
def test_invoice_send_email_without_email(
    order_mock, mock_notify, staff_api_client, permission_manage_orders, order
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
    mock_notify.assert_not_called()
    assert order_mock.called
    errors = content["data"]["invoiceSendNotification"]["invoiceErrors"]
    assert errors == [{"field": "order", "code": "EMAIL_NOT_SET"}]
    assert not order.events.filter(type=OrderEvents.INVOICE_SENT).exists()
