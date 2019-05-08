from datetime import date

import graphene
from tests.api.utils import get_graphql_content


def test_query_own_gift_card(user_api_client, gift_card):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
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
    """
    gift_card_id = graphene.Node.to_global_id('GiftCard', gift_card.pk)
    variables = {'id': gift_card_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['giftCard']
    assert data['code'] == gift_card.code
    assert data['creator']['email'] == gift_card.creator.email
    assert data['created'] == gift_card.created.isoformat()
    assert data['startDate'] == gift_card.start_date.isoformat()
    assert data['expirationDate'] == gift_card.expiration_date
    assert data['lastUsedOn'] == gift_card.last_used_on.isoformat()
    assert data['isActive'] == gift_card.is_active
    assert data['initialBalance']['amount'] == gift_card.initial_balance
    assert data['currentBalance']['amount'] == gift_card.current_balance


def test_query_gift_card_with_premissions(
        staff_api_client, gift_card, permission_manage_gift_card):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            code
            creator {
                email
            }
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id('GiftCard', gift_card.pk)
    variables = {'id': gift_card_id}
    staff_api_client.user.user_permissions.add(permission_manage_gift_card)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['giftCard']
    assert data['code'] == gift_card.code
    assert data['creator']['email'] == gift_card.creator.email


def test_query_gift_card_without_premissions(
        user_api_client, gift_card_created_by_staff):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            code
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id(
        'GiftCard', gift_card_created_by_staff.pk)
    variables = {'id': gift_card_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content['data']['giftCard']


def test_query_gift_cards(
        staff_api_client, gift_card, gift_card_created_by_staff,
        permission_manage_gift_card):
    query = """
    query giftCards{
        giftCards(first: 10) {
            edges {
                node {
                    code
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_gift_card])
    content = get_graphql_content(response)
    data = content['data']['giftCards']['edges']
    assert data[0]['node']['code'] == gift_card.code
    assert data[1]['node']['code'] == gift_card_created_by_staff.code


def test_query_own_gift_cards(
        user_api_client, gift_card, gift_card_created_by_staff):
    query = """
    query giftCards{
        me {
            giftCards(first: 10) {
                edges {
                    node {
                        code
                    }
                }
                totalCount
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content['data']['me']['giftCards']
    assert data['edges'][0]['node']['code'] == gift_card.code
    assert data['totalCount'] == 1
