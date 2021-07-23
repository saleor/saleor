import graphene

# from ....giftcard.error_codes import GiftCardErrorCode
from ...tests.utils import assert_no_permission, get_graphql_content

UPDATE_GIFT_CARD_MUTATION = """
mutation giftCardUpdate(
    $id: ID!, $startDate: Date, $endDate: Date,
    $balance: PriceInput) {
        giftCardUpdate(id: $id, input: {startDate: $startDate,
                endDate: $endDate,
                balance: $balance}) {
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


def test_update_gift_card(
    staff_api_client, gift_card, permission_manage_gift_card, permission_manage_users
):
    balance = 150
    currency = "USD"
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    assert gift_card.current_balance != balance
    assert gift_card.created_by != staff_api_client.user
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
        "balance": {
            "amount": balance,
            "currency": currency,
        },
    }
    response = staff_api_client.post_graphql(
        UPDATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
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
    currency = "USD"
    assert gift_card.code != new_code
    assert gift_card.current_balance != balance
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
        "balance": {
            "amount": balance,
            "currency": currency,
        },
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
