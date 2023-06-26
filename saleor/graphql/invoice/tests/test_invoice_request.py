from unittest.mock import patch

import graphene
import pytest

from ....core import JobStatus
from ....graphql.tests.utils import assert_no_permission, get_graphql_content
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
            errors {
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


@patch(
    "saleor.graphql.invoice.mutations.invoice_request.is_event_active_for_any_plugin",
    return_value=True,
)
@patch("saleor.plugins.manager.PluginsManager.invoice_request")
def test_invoice_request(
    plugin_mock,
    active_event_check_mock,
    staff_api_client,
    permission_group_manage_orders,
    order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    dummy_invoice = Invoice.objects.create(order=order)
    plugin_mock.return_value = dummy_invoice
    number = "01/12/2020/TEST"
    graphene_order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {
        "orderId": graphene_order_id,
        "number": number,
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_REQUEST_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    invoice = Invoice.objects.filter(
        number=number, order=order.pk, status=JobStatus.PENDING
    ).first()
    assert invoice
    plugin_mock.assert_called_once_with(order=order, invoice=invoice, number=number)
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


def test_invoice_request_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    order,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    Invoice.objects.create(order=order)
    number = "01/12/2020/TEST"
    graphene_order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {
        "orderId": graphene_order_id,
        "number": number,
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_REQUEST_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch(
    "saleor.graphql.invoice.mutations.invoice_request.is_event_active_for_any_plugin",
    return_value=True,
)
@patch("saleor.plugins.manager.PluginsManager.invoice_request")
def test_invoice_request_by_app(
    plugin_mock,
    active_event_check_mock,
    app_api_client,
    permission_manage_orders,
    order,
):
    # given
    dummy_invoice = Invoice.objects.create(order=order)
    plugin_mock.return_value = dummy_invoice
    number = "01/12/2020/TEST"
    graphene_order_id = graphene.Node.to_global_id("Order", order.pk)
    variables = {
        "orderId": graphene_order_id,
        "number": number,
    }

    # when
    response = app_api_client.post_graphql(
        INVOICE_REQUEST_MUTATION, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    invoice = Invoice.objects.filter(
        number=number, order=order.pk, status=JobStatus.PENDING
    ).first()
    assert invoice
    plugin_mock.assert_called_once_with(order=order, invoice=invoice, number=number)
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.REQUESTED,
        user=None,
        app=app_api_client.app,
        order=invoice.order,
        parameters__number=number,
    ).exists()
    assert (
        content["data"]["invoiceRequest"]["invoice"]["status"]
        == JobStatus.PENDING.upper()
    )
    assert content["data"]["invoiceRequest"]["order"]["id"] == graphene_order_id
    assert invoice.order.events.filter(
        type=OrderEvents.INVOICE_REQUESTED,
        order=order,
        user=None,
        app=app_api_client.app,
    ).exists()


@pytest.mark.parametrize(
    "status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED, OrderStatus.EXPIRED)
)
def test_invoice_request_invalid_order_status(
    status, staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order.status = status
    order.save()
    number = "01/12/2020/TEST"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_REQUEST_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(number=number, order=order.pk).exists()
    error = content["data"]["invoiceRequest"]["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.INVALID_STATUS.name
    assert not OrderEvent.objects.filter(type=OrderEvents.INVOICE_REQUESTED).exists()


def test_invoice_request_no_billing_address(
    staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order.billing_address = None
    order.save()
    number = "01/12/2020/TEST"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_REQUEST_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(number=number, order=order.pk).exists()
    error = content["data"]["invoiceRequest"]["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.NOT_READY.name
    assert not OrderEvent.objects.filter(type=OrderEvents.INVOICE_REQUESTED).exists()


@patch(
    "saleor.graphql.invoice.mutations.invoice_request.is_event_active_for_any_plugin",
    return_value=True,
)
def test_invoice_request_no_number(
    active_event_check_mock, staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"orderId": graphene.Node.to_global_id("Order", order.pk)}

    # when
    staff_api_client.post_graphql(INVOICE_REQUEST_MUTATION, variables)

    # then
    invoice = Invoice.objects.get(order=order.pk)
    assert invoice.number is None
    assert OrderEvent.objects.filter(type=OrderEvents.INVOICE_REQUESTED).exists()


def test_invoice_request_invalid_id(staff_api_client, permission_group_manage_orders):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "orderId": "T3JkZXI6ZmZmMTVjYjItZTc1OC00MGJhLThkYTktNjE3ZTIwNDhlMGQ2",
        "number": "01/12/2020/TEST",
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_REQUEST_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["invoiceRequest"]["errors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "orderId"


@patch(
    "saleor.graphql.invoice.mutations.invoice_request.is_event_active_for_any_plugin",
    return_value=False,
)
def test_invoice_request_no_invoice_plugin(
    active_event_check_mock, order, permission_group_manage_orders, staff_api_client
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    number = "01/12/2020/TEST"
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "number": number,
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_REQUEST_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not Invoice.objects.filter(number=number, order=order.pk).exists()
    error = content["data"]["invoiceRequest"]["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == InvoiceErrorCode.NO_INVOICE_PLUGIN.name
    assert not OrderEvent.objects.filter(type=OrderEvents.INVOICE_REQUESTED).exists()
