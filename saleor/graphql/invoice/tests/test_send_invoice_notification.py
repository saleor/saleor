from unittest.mock import patch

import graphene

from ....core import JobStatus
from ....core.notify_events import NotifyEventType
from ....graphql.tests.utils import get_graphql_content
from ....invoice.models import Invoice
from ....invoice.notifications import get_invoice_payload
from ....order import OrderEvents
from ...core.utils import to_global_id_or_none

INVOICE_SEND_EMAIL_MUTATION = """
    mutation invoiceSendNotification($id: ID!) {
        invoiceSendNotification(
            id: $id
        ) {
            errors {
                field
                code
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_invoice_send_notification_by_user(
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
    expected_payload = {
        "requester_user_id": to_global_id_or_none(staff_api_client.user),
        "requester_app_id": None,
        "invoice": get_invoice_payload(invoice),
        "recipient_email": invoice.order.get_customer_email(),
        "domain": "mirumee.com",
        "site_name": "mirumee.com",
    }

    mock_notify.assert_called_once_with(
        NotifyEventType.INVOICE_READY,
        expected_payload,
        channel_slug=invoice.order.channel.slug,
    )
    assert not content["data"]["invoiceSendNotification"]["errors"]


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_invoice_send_notification_by_app(
    mock_notify, app_api_client, permission_manage_orders, order
):
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    invoice = Invoice.objects.create(
        order=order, number=number, url=url, status=JobStatus.SUCCESS
    )
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = app_api_client.post_graphql(
        INVOICE_SEND_EMAIL_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    expected_payload = {
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app_api_client.app),
        "invoice": get_invoice_payload(invoice),
        "recipient_email": invoice.order.get_customer_email(),
        "domain": "mirumee.com",
        "site_name": "mirumee.com",
    }

    mock_notify.assert_called_once_with(
        NotifyEventType.INVOICE_READY,
        expected_payload,
        channel_slug=invoice.order.channel.slug,
    )
    assert not content["data"]["invoiceSendNotification"]["errors"]


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
    errors = content["data"]["invoiceSendNotification"]["errors"]
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
    errors = content["data"]["invoiceSendNotification"]["errors"]
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
    errors = content["data"]["invoiceSendNotification"]["errors"]
    assert errors == [{"field": "order", "code": "EMAIL_NOT_SET"}]
    assert not order.events.filter(type=OrderEvents.INVOICE_SENT).exists()
