import graphene

from .....invoice.models import Invoice
from .test_update_metadata import (
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_add_public_metadata_for_invoice(staff_api_client, permission_manage_orders):
    # given
    invoice = Invoice.objects.create(number="1/7/2020")
    invoice_id = graphene.Node.to_global_id("Invoice", invoice.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, invoice_id, "Invoice"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], invoice, invoice_id
    )


def test_add_private_metadata_for_invoice(staff_api_client, permission_manage_orders):
    # given
    invoice = Invoice.objects.create(number="1/7/2020")
    invoice_id = graphene.Node.to_global_id("Invoice", invoice.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, invoice_id, "Invoice"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], invoice, invoice_id
    )
