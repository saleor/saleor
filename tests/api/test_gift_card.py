from datetime import date, timedelta

import graphene
from tests.api.utils import get_graphql_content

from .utils import assert_no_permission


def test_query_own_gift_card(user_api_client, staff_user, gift_card):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            code
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
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["code"] == gift_card.code
    assert data["created"] == gift_card.created.isoformat()
    assert data["startDate"] == gift_card.start_date.isoformat()
    assert data["endDate"] == gift_card.end_date
    assert data["isActive"] == gift_card.is_active
    assert data["initialBalance"]["amount"] == gift_card.initial_balance
    assert data["currentBalance"]["amount"] == gift_card.current_balance


def test_query_gift_card_with_premissions(
    staff_api_client, gift_card, permission_manage_gift_card
):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            code
            user {
                email
            }
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}
    staff_api_client.user.user_permissions.add(permission_manage_gift_card)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["code"] == gift_card.code
    assert data["user"]["email"] == gift_card.user.email


def test_query_gift_card_without_premissions(
    user_api_client, gift_card_created_by_staff
):
    query = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            code
        }
    }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_created_by_staff.pk)
    variables = {"id": gift_card_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["giftCard"]


def test_query_gift_cards(
    staff_api_client, gift_card, gift_card_created_by_staff, permission_manage_gift_card
):
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
        query, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert data[0]["node"]["code"] == gift_card.code
    assert data[1]["node"]["code"] == gift_card_created_by_staff.code


def test_query_own_gift_cards(user_api_client, gift_card, gift_card_created_by_staff):
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
    data = content["data"]["me"]["giftCards"]
    assert data["edges"][0]["node"]["code"] == gift_card.code
    assert data["totalCount"] == 1


CREATE_GIFT_CARD_MUTATION = """
mutation giftCardCreate(
    $code: String, $startDate: Date, $endDate: Date,
    $balance: Decimal!, $userEmail: String) {
        giftCardCreate(input: {
                code: $code, startDate: $startDate,
                endDate: $endDate,
                balance: $balance, userEmail: $userEmail }) {
            errors {
                field
                message
            }
            giftCard {
                code
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


def test_create_gift_card(staff_api_client, customer_user, permission_manage_gift_card):
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
        CREATE_GIFT_CARD_MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardCreate"]["giftCard"]
    assert data["code"] == code
    assert data["user"]["email"] == customer_user.email
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()
    assert not data["lastUsedOn"]
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance


def test_create_gift_card_with_empty_code(
    staff_api_client, permission_manage_gift_card
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
        CREATE_GIFT_CARD_MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardCreate"]["giftCard"]
    assert data["code"] != ""


def test_create_gift_card_without_code(staff_api_client, permission_manage_gift_card):
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
        CREATE_GIFT_CARD_MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardCreate"]["giftCard"]
    assert data["code"] != ""


def test_create_gift_card_with_existing_voucher_code(
    staff_api_client, voucher, permission_manage_gift_card
):
    initial_balance = 123
    variables = {"code": voucher.code, "balance": initial_balance}
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    assert content["data"]["giftCardCreate"]["errors"]
    errors = content["data"]["giftCardCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors[0]["message"] == "Gift card with this code is not available."


def test_create_gift_card_with_existing_gift_card_code(
    staff_api_client, gift_card, permission_manage_gift_card
):
    initial_balance = 123
    variables = {"code": gift_card.code, "balance": initial_balance}
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    assert content["data"]["giftCardCreate"]["errors"]
    errors = content["data"]["giftCardCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors[0]["message"] == "Gift card with this code is not available."


def test_create_gift_card_without_user(staff_api_client, permission_manage_gift_card):
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
        CREATE_GIFT_CARD_MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardCreate"]["giftCard"]
    assert data["code"] == code
    assert not data["user"]


def test_create_gift_card_with_incorrect_user_email(
    staff_api_client, permission_manage_gift_card
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
        "userEmail": "incorrecr@email.com",
    }
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    assert content["data"]["giftCardCreate"]["errors"]
    errors = content["data"]["giftCardCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "Customer with this email doesn't exist."


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


UPDATE_GIFT_CARD_MUTATION = """
mutation giftCardUpdate(
    $id: ID!, $startDate: Date, $endDate: Date,
    $balance: Decimal, $userEmail: String!) {
        giftCardUpdate(id: $id, input: {startDate: $startDate,
                endDate: $endDate,
                balance: $balance, userEmail: $userEmail}) {
            errors {
                field
                message
            }
            giftCard {
                code
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
    data = content["data"]["giftCardUpdate"]["giftCard"]
    assert data["code"] == gift_card.code
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


def test_update_gift_card_update_code_error(
    staff_api_client, gift_card, permission_manage_gift_card
):
    query = """
    mutation giftCardUpdate($id: ID!, $code: String!) {
        giftCardUpdate(id: $id, input: { code: $code }) {
            errors {
                field
                message
            }
            giftCard {
                code
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
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
        "code": "new_code",
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )
    content = get_graphql_content(response)
    assert content["data"]["giftCardUpdate"]["errors"]
    errors = content["data"]["giftCardUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors[0]["message"] == "Cannot update a gift card code."
    assert not content["data"]["giftCardUpdate"]["giftCard"]


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


VERIFY_CODE_GIFT_CARD_MUTATION = """
mutation giftCardVerify($code: String!) {
    giftCardVerify(code: $code){
        errors {
            field
            message
        }
        giftCard{
            code
            currentBalance {
                amount
            }
        }
    }
}
"""


def test_verify_gift_card_code(user_api_client, gift_card):
    variables = {"code": gift_card.code}
    response = user_api_client.post_graphql(VERIFY_CODE_GIFT_CARD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["giftCardVerify"]["giftCard"]
    assert data["code"] == gift_card.code
    assert data["currentBalance"]["amount"] == gift_card.current_balance


def test_verify_gift_card_code_incorect_code(user_api_client):
    variables = {"code": "incorect_code"}
    response = user_api_client.post_graphql(VERIFY_CODE_GIFT_CARD_MUTATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["giftCardVerify"]["errors"]
    errors = content["data"]["giftCardVerify"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors[0]["message"] == "Incorrect gift card code."
    assert not content["data"]["giftCardVerify"]["giftCard"]


def test_verify_gift_card_code_inactive_code(user_api_client, gift_card):
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    variables = {"code": gift_card.code}
    response = user_api_client.post_graphql(VERIFY_CODE_GIFT_CARD_MUTATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["giftCardVerify"]["errors"]
    errors = content["data"]["giftCardVerify"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "isActive"
    assert errors[0]["message"] == "Gift card is inactive."
    assert not content["data"]["giftCardVerify"]["giftCard"]


def test_verify_gift_card_code_expired_code(user_api_client, gift_card):
    gift_card.end_date = date.today() - timedelta(days=3)
    gift_card.save(update_fields=["end_date"])
    variables = {"code": gift_card.code}
    response = user_api_client.post_graphql(VERIFY_CODE_GIFT_CARD_MUTATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["giftCardVerify"]["errors"]
    errors = content["data"]["giftCardVerify"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "endDate"
    assert errors[0]["message"] == "Gift card expired."
    assert not content["data"]["giftCardVerify"]["giftCard"]
