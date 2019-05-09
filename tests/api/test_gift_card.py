from datetime import date

import graphene
from tests.api.utils import get_graphql_content

from .utils import assert_no_permission


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


CREATE_GIFT_CARD_MUTATION = """
mutation giftCardCreate(
    $code: String, $startDate: Date, $expirationDate: Date,
    $initialBalance: Decimal) {
        giftCardCreate(input: {
                code: $code, startDate: $startDate,
                expirationDate: $expirationDate,
                initialBalance: $initialBalance}) {
            errors {
                field
                message
            }
            giftCard {
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
"""


def test_create_gift_card(staff_api_client, permission_manage_gift_card):
    code = 'mirumee'
    start_date = date(day=1, month=1, year=2018)
    expiration_date = date(day=1, month=1, year=2019)
    initial_balance = 100
    variables = {
        'code': code,
        'startDate': start_date.isoformat(),
        'expirationDate': expiration_date.isoformat(),
        'initialBalance': initial_balance}
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card])
    content = get_graphql_content(response)
    data = content['data']['giftCardCreate']['giftCard']
    assert data['code'] == code
    assert data['creator']['email'] == staff_api_client.user.email
    assert data['startDate'] == start_date.isoformat()
    assert data['expirationDate'] == expiration_date.isoformat()
    assert data['lastUsedOn'] == date.today().isoformat()
    assert data['isActive']
    assert data['initialBalance']['amount'] == initial_balance
    assert data['currentBalance']['amount'] == initial_balance


def test_create_gift_card_with_empty_code(
        staff_api_client, permission_manage_gift_card):
    start_date = date(day=1, month=1, year=2018)
    expiration_date = date(day=1, month=1, year=2019)
    initial_balance = 123
    variables = {
        'code': "",
        'startDate': start_date.isoformat(),
        'expirationDate': expiration_date.isoformat(),
        'initialBalance': initial_balance}
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card])
    content = get_graphql_content(response)
    data = content['data']['giftCardCreate']['giftCard']
    assert data['code'] != ''


def test_create_gift_card_without_premissions(staff_api_client):
    code = 'mirumee'
    start_date = date(day=1, month=1, year=2018)
    expiration_date = date(day=1, month=1, year=2019)
    initial_balance = 100
    variables = {
        'code': code,
        'startDate': start_date.isoformat(),
        'expirationDate': expiration_date.isoformat(),
        'initialBalance': initial_balance}
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION, variables)
    assert_no_permission(response)
