from datetime import date

import graphene

from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_GIFT_CARD_BY_ID = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            id
            code
            last4CodeChars
            user {
                email
            }
            endDate
            startDate
        }
    }
"""


def test_query_gift_card(
    staff_api_client, gift_card, permission_manage_gift_card, permission_manage_users
):
    query = QUERY_GIFT_CARD_BY_ID

    end_date = date(day=1, month=1, year=2018)
    gift_card.expiry_date = end_date
    gift_card.save(update_fields=["expiry_date"])

    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["id"] == gift_card_id
    assert data["last4CodeChars"] == gift_card.display_code
    assert data["user"]["email"] == gift_card.created_by.email
    assert data["endDate"] == end_date.isoformat()
    assert data["startDate"] is None


def test_query_gift_card_no_permission(staff_api_client, gift_card):
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    # Query should fail without manage_users permission.
    response = staff_api_client.post_graphql(query, variables)

    assert_no_permission(response)
