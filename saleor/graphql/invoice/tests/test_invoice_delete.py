from unittest.mock import patch

import graphene

from ....graphql.tests.utils import get_graphql_content
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.models import Invoice, InvoiceEvent, InvoiceEvents

INVOICE_DELETE_MUTATION = """
    mutation invoiceDelete($id: ID!) {
        invoiceDelete(
            id: $id
        ) {
            errors {
                field
                code
            }
        }
    }
"""


def test_invoice_delete(staff_api_client, permission_manage_orders, order):
    invoice = Invoice.objects.create(order=order)
    variables = {"id": graphene.Node.to_global_id("Invoice", invoice.pk)}
    response = staff_api_client.post_graphql(
        INVOICE_DELETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["invoiceDelete"]["errors"]
    assert not Invoice.objects.filter(id=invoice.pk).exists()
    assert InvoiceEvent.objects.filter(
        type=InvoiceEvents.DELETED,
        user=staff_api_client.user,
        parameters__invoice_id=invoice.id,
    ).exists()


@patch("saleor.plugins.manager.PluginsManager.invoice_delete")
def test_invoice_delete_invalid_id(
    plugin_mock, staff_api_client, permission_manage_orders
):
    variables = {"id": graphene.Node.to_global_id("Invoice", 1337)}
    response = staff_api_client.post_graphql(
        INVOICE_DELETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["invoiceDelete"]["errors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "id"
    plugin_mock.assert_not_called()
