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


def test_delete_private_metadata_for_gift_card(
    staff_api_client, permission_manage_gift_card, gift_card
):
    # given
    gift_card.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    gift_card.save(update_fields=["private_metadata"])
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_gift_card, gift_card_id, "GiftCard"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], gift_card, gift_card_id
    )


def test_delete_public_metadata_for_gift_card(
    staff_api_client, permission_manage_gift_card, gift_card
):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_gift_card, gift_card_id, "GiftCard"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], gift_card, gift_card_id
    )


def test_add_public_metadata_for_gift_card(
    staff_api_client, permission_manage_gift_card, gift_card
):
    # given
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_gift_card, gift_card_id, "GiftCard"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], gift_card, gift_card_id
    )


def test_add_private_metadata_for_gift_card(
    staff_api_client, permission_manage_gift_card, gift_card
):
    # given
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_gift_card, gift_card_id, "GiftCard"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], gift_card, gift_card_id
    )
