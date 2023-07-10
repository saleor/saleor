import graphene

from ....core import JobStatus
from ....graphql.tests.utils import assert_no_permission, get_graphql_content
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.models import Invoice

INVOICE_UPDATE_MUTATION = """
    mutation invoiceUpdate($id: ID!, $input: UpdateInvoiceInput!) {
        invoiceUpdate(
            id: $id
            input: $input
        ) {
            invoice {
                id
                number
                url
                metadata {
                    key
                    value
                }
                privateMetadata {
                    key
                    value
                }
            }
            errors {
                field
                code
            }
        }
    }
"""


def test_invoice_update(staff_api_client, permission_group_manage_orders, order):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    test_key = "test_key"
    metadata = {test_key: "test_val"}
    invoice = Invoice.objects.create(order=order, metadata=metadata)
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    graphene_invoice_id = graphene.Node.to_global_id("Invoice", invoice.pk)
    variables = {
        "id": graphene_invoice_id,
        "input": {
            "number": number,
            "url": url,
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    assert invoice.status == JobStatus.SUCCESS
    assert invoice.number == content["data"]["invoiceUpdate"]["invoice"]["number"]
    response_metadata = content["data"]["invoiceUpdate"]["invoice"]["metadata"][0]
    assert response_metadata["key"] == test_key
    assert response_metadata["value"] == metadata[test_key]
    assert invoice.url == content["data"]["invoiceUpdate"]["invoice"]["url"]
    assert content["data"]["invoiceUpdate"]["invoice"]["id"] == graphene_invoice_id


def test_invoice_update_by_user_no_channel_access(
    staff_api_client, permission_group_all_perms_channel_USD_only, order, channel_PLN
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    test_key = "test_key"
    metadata = {test_key: "test_val"}
    invoice = Invoice.objects.create(order=order, metadata=metadata)
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    graphene_invoice_id = graphene.Node.to_global_id("Invoice", invoice.pk)
    variables = {
        "id": graphene_invoice_id,
        "input": {
            "number": number,
            "url": url,
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_invoice_update_by_app(app_api_client, permission_manage_orders, order):
    # given
    test_key = "test_key"
    metadata = {test_key: "test_val"}
    invoice = Invoice.objects.create(order=order, metadata=metadata)
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    graphene_invoice_id = graphene.Node.to_global_id("Invoice", invoice.pk)
    new_metadata = [{"key": test_key, "value": "test value"}]
    private_metadata = [{"key": "private test key", "value": "private test value"}]
    variables = {
        "id": graphene_invoice_id,
        "input": {
            "number": number,
            "url": url,
            "metadata": new_metadata,
            "privateMetadata": private_metadata,
        },
    }

    # when
    response = app_api_client.post_graphql(
        INVOICE_UPDATE_MUTATION, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    assert invoice.status == JobStatus.SUCCESS
    assert invoice.number == content["data"]["invoiceUpdate"]["invoice"]["number"]
    assert content["data"]["invoiceUpdate"]["invoice"]["metadata"] == new_metadata
    assert (
        content["data"]["invoiceUpdate"]["invoice"]["privateMetadata"]
        == private_metadata
    )
    assert invoice.url == content["data"]["invoiceUpdate"]["invoice"]["url"]
    assert content["data"]["invoiceUpdate"]["invoice"]["id"] == graphene_invoice_id


def test_invoice_update_single_value(
    staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    number = "01/12/2020/TEST"
    invoice = Invoice.objects.create(order=order, number=number)
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("Invoice", invoice.pk),
        "input": {
            "url": url,
        },
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    assert invoice.status == JobStatus.SUCCESS
    assert invoice.number == number
    assert invoice.url == content["data"]["invoiceUpdate"]["invoice"]["url"]


def test_invoice_update_missing_number(
    staff_api_client, permission_group_manage_orders, order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    invoice = Invoice.objects.create(order=order)
    url = "http://www.example.com"
    variables = {
        "id": graphene.Node.to_global_id("Invoice", invoice.pk),
        "input": {"url": url},
    }

    # when
    response = staff_api_client.post_graphql(INVOICE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    invoice.refresh_from_db()
    error = content["data"]["invoiceUpdate"]["errors"][0]
    assert error["code"] == InvoiceErrorCode.NUMBER_NOT_SET.name
    assert error["field"] == "number"
    assert invoice.url is None
    assert invoice.status == JobStatus.PENDING


def test_invoice_update_invalid_id(staff_api_client, permission_group_manage_orders):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": "SW52b2ljZToxMzM3", "input": {"number": "01/12/2020/TEST"}}

    # when
    response = staff_api_client.post_graphql(INVOICE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["invoiceUpdate"]["errors"][0]
    assert error["code"] == InvoiceErrorCode.NOT_FOUND.name
    assert error["field"] == "id"
