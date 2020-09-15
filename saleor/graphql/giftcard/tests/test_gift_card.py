from datetime import date

import graphene

from ....giftcard.error_codes import GiftCardErrorCode
from ...tests.utils import assert_no_permission, get_graphql_content


def test_query_gift_card_with_permissions(
    staff_api_client, gift_card, permission_manage_gift_card, permission_manage_users
):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            id
            displayCode
            user {
                email
            }
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    # Query should fail without manage_users permission.
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )
    assert_no_permission(response)

    # Query should succeed with manage_users and manage_gift_card permissions.
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["id"] == gift_card_id
    assert data["displayCode"] == gift_card.display_code
    assert data["user"]["email"] == gift_card.user.email


def test_query_gift_card_code_without_user(
    staff_api_client,
    gift_card_created_by_staff,
    permission_manage_gift_card,
    permission_manage_users,
):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            id
            displayCode
            code
            user{
                email
            }
        }
    }
    """
    gift_card = gift_card_created_by_staff
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
    assert data["displayCode"] == gift_card.display_code
    assert data["code"] == gift_card.code
    assert not data["user"]


def test_query_gift_card_code_with_user(
    staff_api_client, gift_card, permission_manage_gift_card, permission_manage_users
):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            id
            displayCode
            code
            user{
                email
            }
        }
    }
    """
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
    assert data["displayCode"] == gift_card.display_code
    assert data["user"]["email"]
    assert not data["code"]


def test_query_gift_card_without_premissions(
    user_api_client, gift_card_created_by_staff
):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            id
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_created_by_staff.pk)
    variables = {"id": gift_card_id}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_query_gift_cards(
    staff_api_client, gift_card, gift_card_created_by_staff, permission_manage_gift_card
):
    query = """
    query giftCards{
        giftCards(first: 10) {
            edges {
                node {
                    id
                    displayCode
                }
            }
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    gift_card_created_by_staff_id = graphene.Node.to_global_id(
        "GiftCard", gift_card_created_by_staff.pk
    )
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert data[0]["node"]["id"] == gift_card_id
    assert data[0]["node"]["displayCode"] == gift_card.display_code
    assert data[1]["node"]["id"] == gift_card_created_by_staff_id
    assert data[1]["node"]["displayCode"] == gift_card_created_by_staff.display_code


def test_query_own_gift_cards(user_api_client, gift_card, gift_card_created_by_staff):
    query = """
    query giftCards{
        me {
            giftCards(first: 10) {
                edges {
                    node {
                        id
                        displayCode
                        code
                    }
                }
                totalCount
            }
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["me"]["giftCards"]
    assert data["edges"][0]["node"]["id"] == gift_card_id
    assert data["edges"][0]["node"]["displayCode"] == gift_card.display_code
    assert data["edges"][0]["node"]["code"] == gift_card.code
    assert data["totalCount"] == 1


def test_query_gift_card_by_app_with_permissions(
    app_api_client, gift_card, permission_manage_gift_card, permission_manage_users
):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            id
            displayCode
            user {
                email
            }
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    # Query should fail without manage_users permission.
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )
    assert_no_permission(response)

    # Query should succeed with manage_users and manage_gift_card permissions.
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["id"] == gift_card_id
    assert data["displayCode"] == gift_card.display_code
    assert data["user"]["email"] == gift_card.user.email


def test_query_gift_card_by_app_without_premissions(
    app_api_client, gift_card_created_by_staff
):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            id
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_created_by_staff.pk)
    variables = {"id": gift_card_id}
    response = app_api_client.post_graphql(query, variables)
    assert_no_permission(response)


CREATE_GIFT_CARD_MUTATION = """
mutation giftCardCreate(
    $code: String, $startDate: Date, $endDate: Date,
    $balance: PositiveDecimal!, $userEmail: String) {
        giftCardCreate(input: {
                code: $code, startDate: $startDate,
                endDate: $endDate,
                balance: $balance, userEmail: $userEmail }) {
            errors {
                field
                message
            }
            giftCardErrors {
                field
                message
                code
            }
            giftCard {
                displayCode
                user {
                    email
                }
                created
                startDate
                endDate
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


def test_create_gift_card(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
):
    code = "mirumee"
    start_date = date(day=1, month=1, year=2018)
    end_date = date(day=1, month=1, year=2019)
    initial_balance = 100
    variables = {
        "code": code,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "balance": initial_balance,
        "userEmail": customer_user.email,
    }
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["displayCode"]
    assert data["user"]["email"] == customer_user.email
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()
    assert not data["lastUsedOn"]
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance


def test_create_gift_card_with_empty_code(
    staff_api_client, permission_manage_gift_card, permission_manage_users
):
    start_date = date(day=1, month=1, year=2018)
    end_date = date(day=1, month=1, year=2019)
    initial_balance = 123
    variables = {
        "code": "",
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "balance": initial_balance,
        "userEmail": staff_api_client.user.email,
    }
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert len(data["displayCode"]) > 4


def test_create_gift_card_without_code(
    staff_api_client, permission_manage_gift_card, permission_manage_users
):
    start_date = date(day=1, month=1, year=2018)
    end_date = date(day=1, month=1, year=2019)
    initial_balance = 123
    variables = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "balance": initial_balance,
        "userEmail": staff_api_client.user.email,
    }
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert len(data["displayCode"]) > 4


def test_create_gift_card_with_existing_voucher_code(
    staff_api_client, voucher, permission_manage_gift_card, permission_manage_users
):
    initial_balance = 123
    variables = {"code": voucher.code, "balance": initial_balance}
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    assert content["data"]["giftCardCreate"]["errors"]
    errors = content["data"]["giftCardCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "promoCode"

    gift_card_errors = content["data"]["giftCardCreate"]["giftCardErrors"]
    assert gift_card_errors[0]["code"] == GiftCardErrorCode.ALREADY_EXISTS.name


def test_create_gift_card_with_existing_gift_card_code(
    staff_api_client, gift_card, permission_manage_gift_card, permission_manage_users
):
    initial_balance = 123
    variables = {"code": gift_card.code, "balance": initial_balance}
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    assert content["data"]["giftCardCreate"]["errors"]
    errors = content["data"]["giftCardCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "promoCode"

    gift_card_errors = content["data"]["giftCardCreate"]["giftCardErrors"]
    assert gift_card_errors[0]["code"] == GiftCardErrorCode.ALREADY_EXISTS.name


def test_create_gift_card_without_user(
    staff_api_client, permission_manage_gift_card, permission_manage_users
):
    code = "mirumee1"
    start_date = date(day=1, month=1, year=2018)
    end_date = date(day=1, month=1, year=2019)
    initial_balance = 123
    variables = {
        "code": code,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "balance": initial_balance,
        "userEmail": "",
    }
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance
    assert not data["user"]


def test_create_gift_card_with_incorrect_user_email(
    staff_api_client, permission_manage_gift_card, permission_manage_users
):
    code = "mirumee1"
    start_date = date(day=1, month=1, year=2018)
    end_date = date(day=1, month=1, year=2019)
    initial_balance = 123
    variables = {
        "code": code,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "balance": initial_balance,
        "userEmail": "incorrect@email.com",
    }
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "Customer with this email doesn't exist."

    gift_card_errors = content["data"]["giftCardCreate"]["giftCardErrors"]
    assert gift_card_errors[0]["code"] == GiftCardErrorCode.NOT_FOUND.name


def test_create_gift_card_without_premissions(staff_api_client):
    code = "mirumee"
    start_date = date(day=1, month=1, year=2018)
    end_date = date(day=1, month=1, year=2019)
    initial_balance = 100
    variables = {
        "code": code,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "balance": initial_balance,
        "userEmail": staff_api_client.user.email,
    }
    response = staff_api_client.post_graphql(CREATE_GIFT_CARD_MUTATION, variables)
    assert_no_permission(response)


def test_create_gift_card_with_to_many_decimal_places_in_amount(
    staff_api_client, permission_manage_gift_card, permission_manage_users
):
    start_date = date(day=1, month=1, year=2018)
    end_date = date(day=1, month=1, year=2019)
    initial_balance = 10.123
    variables = {
        "code": "test12",
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "balance": initial_balance,
        "userEmail": staff_api_client.user.email,
    }
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["giftCardErrors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "balance"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


UPDATE_GIFT_CARD_MUTATION = """
mutation giftCardUpdate(
    $id: ID!, $startDate: Date, $endDate: Date,
    $balance: PositiveDecimal, $userEmail: String!) {
        giftCardUpdate(id: $id, input: {startDate: $startDate,
                endDate: $endDate,
                balance: $balance, userEmail: $userEmail}) {
            errors {
                field
                message
            }
            giftCard {
                id
                displayCode
                currentBalance {
                    amount
                }
                user {
                    email
                }
            }
        }
    }
"""


def test_update_gift_card(staff_api_client, gift_card, permission_manage_gift_card):
    balance = 150
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    assert gift_card.current_balance != balance
    assert gift_card.user != staff_api_client.user
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
        "balance": balance,
        "userEmail": staff_api_client.user.email,
    }
    response = staff_api_client.post_graphql(
        UPDATE_GIFT_CARD_MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["id"] == gift_card_id
    assert data["displayCode"] == gift_card.display_code
    assert data["currentBalance"]["amount"] == balance
    assert data["user"]["email"] == staff_api_client.user.email


def test_update_gift_card_without_premissions(staff_api_client, gift_card):
    new_code = "new_test_code"
    balance = 150
    assert gift_card.code != new_code
    assert gift_card.current_balance != balance
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
        "balance": balance,
        "userEmail": staff_api_client.user.email,
    }

    response = staff_api_client.post_graphql(UPDATE_GIFT_CARD_MUTATION, variables)
    assert_no_permission(response)


DEACTIVATE_GIFT_CARD_MUTATION = """
mutation giftCardDeactivate($id: ID!) {
    giftCardDeactivate(id: $id) {
        errors {
            field
            message
        }
        giftCard {
            isActive
        }
    }
}
"""


def test_deactivate_gift_card(staff_api_client, gift_card, permission_manage_gift_card):
    assert gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(
        DEACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardDeactivate"]["giftCard"]
    assert not data["isActive"]


def test_deactivate_gift_card_without_premissions(staff_api_client, gift_card):
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(DEACTIVATE_GIFT_CARD_MUTATION, variables)
    assert_no_permission(response)


def test_deactivate_gift_card_inactive_gift_card(
    staff_api_client, gift_card, permission_manage_gift_card
):
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    assert not gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(
        DEACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardDeactivate"]["giftCard"]
    assert not data["isActive"]


ACTIVATE_GIFT_CARD_MUTATION = """
mutation giftCardActivate($id: ID!) {
    giftCardActivate(id: $id) {
        errors {
            field
            message
        }
        giftCard {
            isActive
        }
    }
}
"""


def test_activate_gift_card(staff_api_client, gift_card, permission_manage_gift_card):
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    assert not gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardActivate"]["giftCard"]
    assert data["isActive"]


def test_activate_gift_card_without_premissions(staff_api_client, gift_card):
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(ACTIVATE_GIFT_CARD_MUTATION, variables)
    assert_no_permission(response)


def test_activate_gift_card_active_gift_card(
    staff_api_client, gift_card, permission_manage_gift_card
):
    assert gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardActivate"]["giftCard"]
    assert data["isActive"]
