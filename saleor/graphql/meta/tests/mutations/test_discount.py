import graphene

from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE
from .test_delete_metadata import (
    execute_clear_public_metadata_for_item,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_delete_public_metadata_for_voucher(
    staff_api_client, permission_manage_discounts, voucher
):
    # given
    voucher.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    voucher.save(update_fields=["metadata"])
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_discounts, voucher_id, "Voucher"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], voucher, voucher_id
    )


def test_delete_public_metadata_for_sale(
    staff_api_client, permission_manage_discounts, sale
):
    # given
    sale.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    sale.save(update_fields=["metadata"])
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_discounts, sale_id, "Sale"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], sale, sale_id
    )


def test_delete_private_metadata_for_voucher(
    staff_api_client, permission_manage_discounts, voucher
):
    # given
    voucher.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    voucher.save(update_fields=["private_metadata"])
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_discounts, voucher_id, "Voucher"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], voucher, voucher_id
    )


def test_delete_private_metadata_for_sale(
    staff_api_client, permission_manage_discounts, sale
):
    # given
    sale.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    sale.save(update_fields=["private_metadata"])
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_discounts, sale_id, "Sale"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], sale, sale_id
    )


def test_add_public_metadata_for_voucher(
    staff_api_client, permission_manage_discounts, voucher
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_discounts, voucher_id, "Voucher"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], voucher, voucher_id
    )


def test_add_private_metadata_for_sale(
    staff_api_client, permission_manage_discounts, sale
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_discounts, sale_id, "Sale"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], sale, sale_id
    )


def test_add_private_metadata_for_voucher(
    staff_api_client, permission_manage_discounts, voucher
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_discounts, voucher_id, "Voucher"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], voucher, voucher_id
    )
