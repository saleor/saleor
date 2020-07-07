import graphene

from ....core import JobStatus
from ....graphql.tests.utils import get_graphql_content
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.models import Invoice

INVOICE_UPDATE_MUTATION = """
    mutation invoiceUpdate($id: ID!, $number: String, $url: String) {
        invoiceUpdate(
            id: $id
            input: {
                number: $number
                url: $url
            }
        ) {
            invoice {
                id
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


def test_invoice_update(staff_api_client, permission_manage_orders, order):
    test_key = "test_key"
    metadata = {test_key: "test_val"}
    invoice = Invoice.objects.create(order=order, metadata=metadata)
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    graphene_invoice_id = graphene.Node.to_global_id("Invoice", invoice.pk)
    variables = {
        "id": graphene_invoice_id,
        "number": number,
        "url": url,
    }
    response = staff_api_client.post_graphql(
        INVOICE_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    assert invoice.status == JobStatus.SUCCESS
    assert invoice.number == content["data"]["invoiceUpdate"]["invoice"]["number"]
    response_metadata = content["data"]["invoiceUpdate"]["invoice"]["metadata"][0]
    assert response_metadata["key"] == test_key
    assert response_metadata["value"] == metadata[test_key]
    assert invoice.url == content["data"]["invoiceUpdate"]["invoice"]["url"]
    assert content["data"]["invoiceUpdate"]["invoice"]["id"] == graphene_invoice_id


def test_invoice_update_single_value(staff_api_client, permission_manage_orders, order):
    number = "01/12/2020/TEST"
    invoice = Invoice.objects.create(order=order, number=number)
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("Invoice", invoice.pk),
        "url": url,
    }
    response = staff_api_client.post_graphql(
        INVOICE_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    assert invoice.status == JobStatus.SUCCESS
    assert invoice.number == number
    assert invoice.url == content["data"]["invoiceUpdate"]["invoice"]["url"]


def test_invoice_update_missing_number(
    staff_api_client, permission_manage_orders, order
):
    invoice = Invoice.objects.create(order=order)
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("Invoice", invoice.pk),
        "url": url,
    }
    response = staff_api_client.post_graphql(
        INVOICE_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    error = content["data"]["invoiceUpdate"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NUMBER_NOT_SET.name
    assert error["field"] == "number"
    assert invoice.url is None
    assert invoice.status == JobStatus.PENDING


def test_invoice_update_invalid_id(staff_api_client, permission_manage_orders):
    variables = {"id": "SW52b2ljZToxMzM3", "number": "01/12/2020/TEST"}
    response = staff_api_client.post_graphql(
        INVOICE_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["invoiceUpdate"]["invoiceErrors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "id"
