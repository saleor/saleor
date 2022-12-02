from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_GIFT_CARD_TAGS = """
    query giftCardTags{
        giftCardTags(first: 10) {
            edges {
                node {
                    id
                    name
                }
            }
            totalCount
        }
    }
"""


def test_query_gift_card_tags_by_staff(
    staff_api_client, gift_card_tag_list, permission_manage_gift_card
):
    # given
    query = QUERY_GIFT_CARD_TAGS

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardTags"]["edges"]
    assert len(data) == len(gift_card_tag_list)
    assert {tag["node"]["name"] for tag in data} == {
        tag.name for tag in gift_card_tag_list
    }


def test_query_gift_card_tags_by_app(
    app_api_client, gift_card_tag_list, permission_manage_gift_card
):
    # given
    query = QUERY_GIFT_CARD_TAGS

    # when
    response = app_api_client.post_graphql(
        query, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardTags"]["edges"]
    assert len(data) == len(gift_card_tag_list)
    assert {tag["node"]["name"] for tag in data} == {
        tag.name for tag in gift_card_tag_list
    }


def test_query_gift_card_tags_by_customer(api_client, gift_card_tag_list):
    # given
    query = QUERY_GIFT_CARD_TAGS

    # when
    response = api_client.post_graphql(query)

    # then
    assert_no_permission(response)
