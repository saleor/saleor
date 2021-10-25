from unittest.mock import patch

import graphene
import pytest

from ....graphql.tests.utils import assert_no_permission, get_graphql_content
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.models import Invoice, InvoiceEvent, InvoiceEvents

INVOICE_REQUEST_DELETE_MUTATION = """
    mutation invoiceRequestDelete($id: ID!) {
        invoiceRequestDelete(
            id: $id
        ) {
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


@patch("saleor.plugins.manager.PluginsManager.invoice_delete")
def test_invoice_request_delete(
    plugin_mock, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(order=order)
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(INVOICE_REQUEST_DELETE_MUTATION, variables)
    invoice.refresh_from_db()
    plugin_mock.assert_called_once_with(invoice)
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.REQUESTED_DELETION,
        user=staff_api_client.user,
        invoice=invoice,
        order=invoice.order,
    ).exists()


@patch("saleor.plugins.manager.PluginsManager.invoice_delete")
def test_invoice_request_delete_invalid_id(
    plugin_mock, staff_api_client, permission_manage_orders
):
    variables = {"id": graphene.Node.to_global_id("Invoice", 1337)}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(INVOICE_REQUEST_DELETE_MUTATION, variables)
    content = get_graphql_content(response)
    error = content["data"]["invoiceRequestDelete"]["errors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "id"
    plugin_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.invoice_delete")
def test_invoice_request_delete_no_permission(
    plugin_mock, staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(order=order)
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(INVOICE_REQUEST_DELETE_MUTATION, variables)
    assert_no_permission(response)
    plugin_mock.assert_not_called()
