import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

QUERY_GIFT_CARD_PRIVATE_META = """
    query giftCardMeta($id: ID!){
        giftCard(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_gift_card_as_anonymous_user(api_client, gift_card):
    # given
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_GIFT_CARD_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_gift_card_as_customer(user_api_client, gift_card):
    # given
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_GIFT_CARD_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_gift_card_as_staff(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    gift_card.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_PRIVATE_META,
        variables,
        [permission_manage_gift_card],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["giftCard"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_gift_card_as_app(
    app_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    gift_card.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_GIFT_CARD_PRIVATE_META,
        variables,
        [permission_manage_gift_card],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["giftCard"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_GIFT_CARD_PUBLIC_META = """
    query giftCardMeta($id: ID!){
        giftCard(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_gift_card_as_anonymous_user(api_client, gift_card):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = api_client.post_graphql(QUERY_GIFT_CARD_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_gift_card_as_customer(user_api_client, gift_card):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_GIFT_CARD_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_gift_card_as_staff(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_PUBLIC_META,
        variables,
        [permission_manage_gift_card],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["giftCard"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_gift_card_as_app(
    app_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_GIFT_CARD_PUBLIC_META,
        variables,
        [permission_manage_gift_card],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["giftCard"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE
