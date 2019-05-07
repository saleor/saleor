import graphene
from tests.api.utils import get_graphql_content

from .utils import assert_no_permission


def test_query_gift_cards(
        staff_api_client, gift_card, permission_manage_giftcard):
    query = """
    query giftCards{
        giftCards(first: 1) {
            edges {
                node {
                    code
                    creator {
                        email
                    }
                    created
                    startDate
                    expirationDate
                    lastUsedOn
                    isActive
                    initialBalance {
                        amount
                    }
                    currentBalance {
                        amount
                    }
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_giftcard])
    content = get_graphql_content(response)
    data = content['data']['giftCards']['edges'][0]['node']
    assert data['code'] == gift_card.code
    assert data['creator']['email'] == gift_card.creator.email
    assert data['created'] == gift_card.created.isoformat()
    assert data['startDate'] == gift_card.start_date.isoformat()
    assert data['expirationDate'] == gift_card.expiration_date
    assert data['lastUsedOn'] == gift_card.last_used_on.isoformat()
    assert data['isActive'] == gift_card.is_active
    assert data['initialBalance']['amount'] == gift_card.initial_balance
    assert data['currentBalance']['amount'] == gift_card.current_balance


def test_query_gift_card(
        staff_api_client, gift_card, permission_manage_giftcard):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            code
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id('GiftCard', gift_card.pk)
    variables = {'id': gift_card_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_giftcard])
    content = get_graphql_content(response)
    data = content['data']['giftCard']
    assert data['code'] == gift_card.code


def test_query_gift_card_without_premissions(staff_api_client, gift_card):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            code
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id('GiftCard', gift_card.pk)
    variables = {'id': gift_card_id}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
