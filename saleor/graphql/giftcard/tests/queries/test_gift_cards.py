import graphene
import pytest

from ....tests.utils import get_graphql_content

QUERY_GIFT_CARDS = """
    query giftCards{
        giftCards(first: 10) {
            edges {
                node {
                    id
                    last4CodeChars
                }
            }
            totalCount
        }
    }
"""


def test_query_gift_cards_by_staff(
    staff_api_client, gift_card, gift_card_created_by_staff, permission_manage_gift_card
):
    # given
    query = QUERY_GIFT_CARDS
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    gift_card_created_by_staff_id = graphene.Node.to_global_id(
        "GiftCard", gift_card_created_by_staff.pk
    )

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 2
    assert data[0]["node"]["id"] == gift_card_created_by_staff_id
    assert data[0]["node"]["last4CodeChars"] == gift_card_created_by_staff.display_code
    assert data[1]["node"]["id"] == gift_card_id
    assert data[1]["node"]["last4CodeChars"] == gift_card.display_code


def test_query_gift_cards_by_app(
    app_api_client, gift_card, gift_card_created_by_staff, permission_manage_gift_card
):
    # given
    query = QUERY_GIFT_CARDS
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    gift_card_created_by_staff_id = graphene.Node.to_global_id(
        "GiftCard", gift_card_created_by_staff.pk
    )

    # when
    response = app_api_client.post_graphql(
        query, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 2
    assert data[0]["node"]["id"] == gift_card_created_by_staff_id
    assert data[0]["node"]["last4CodeChars"] == gift_card_created_by_staff.display_code
    assert data[1]["node"]["id"] == gift_card_id
    assert data[1]["node"]["last4CodeChars"] == gift_card.display_code


def test_query_own_gift_cards(
    user_api_client, gift_card_used, gift_card_created_by_staff
):
    query = """
        query giftCards{
            me {
                giftCards(first: 10) {
                    edges {
                        node {
                            id
                            last4CodeChars
                            code
                        }
                    }
                    totalCount
                }
            }
        }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_used.pk)
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["me"]["giftCards"]
    assert data["edges"][0]["node"]["id"] == gift_card_id
    assert data["edges"][0]["node"]["last4CodeChars"] == gift_card_used.display_code
    assert data["edges"][0]["node"]["code"] == gift_card_used.code
    assert data["totalCount"] == 1


ME_GIFT_CARDS = """
    query { me { giftCards(first: 10) { edges { node { id } } } } }
"""


def test_me_gift_cards_includes_assigned(user_api_client, gift_card, customer_user):
    # given
    gift_card.used_by = None
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["used_by", "assigned_to", "assigned_to_email"])

    # when
    response = user_api_client.post_graphql(ME_GIFT_CARDS, {})

    # then
    edges = get_graphql_content(response)["data"]["me"]["giftCards"]["edges"]
    ids = {e["node"]["id"] for e in edges}
    assert graphene.Node.to_global_id("GiftCard", gift_card.pk) in ids


ME_ASSIGNED_FIELD = """
    query MeAssignedField {
        me {
            giftCards(first: 10) {
                edges { node { id %s } }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("field", "extract"),
    [
        ("assignedTo { email }", lambda node: node["assignedTo"]["email"]),
        ("assignedToEmail", lambda node: node["assignedToEmail"]),
    ],
)
def test_me_gift_cards_assigned_field_visible_to_owner(
    field, extract, user_api_client, gift_card, customer_user
):
    # given each assignment field is queried in isolation so a broken
    # authorization check on one cannot be masked by the other
    gift_card.used_by = None
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["used_by", "assigned_to", "assigned_to_email"])
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when the owner queries without MANAGE_USERS / MANAGE_GIFT_CARD permissions
    response = user_api_client.post_graphql(ME_ASSIGNED_FIELD % field, {})

    # then the owner can read the field
    edges = get_graphql_content(response)["data"]["me"]["giftCards"]["edges"]
    node = next(e["node"] for e in edges if e["node"]["id"] == gift_card_id)
    assert extract(node) == customer_user.email


CODE_QUERY = """
    query { me { giftCards(first: 10) { edges { node { id code } } } } }
"""


def test_assigned_customer_can_read_code(user_api_client, gift_card, customer_user):
    # given (user_api_client is authenticated as customer_user)
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.used_by = None
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "used_by"])
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = user_api_client.post_graphql(CODE_QUERY, {})

    # then
    edges = get_graphql_content(response)["data"]["me"]["giftCards"]["edges"]
    node = next(e["node"] for e in edges if e["node"]["id"] == gift_card_id)
    assert node["code"] == gift_card.code


FILTER_QUERY = """
    query GiftCards($filter: GiftCardFilterInput!) {
        giftCards(first: 10, filter: $filter) {
            edges { node { id } }
        }
    }
"""


def test_filter_by_assigned_to(
    staff_api_client,
    gift_card,
    gift_card_created_by_staff,
    customer_user,
    permission_manage_gift_card,
):
    # given a card assigned to the customer and another card assigned to nobody
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])
    variables = {
        "filter": {"assignedTo": [graphene.Node.to_global_id("User", customer_user.pk)]}
    }

    # when
    response = staff_api_client.post_graphql(
        FILTER_QUERY, variables, permissions=[permission_manage_gift_card]
    )

    # then only the matching card is returned
    edges = get_graphql_content(response)["data"]["giftCards"]["edges"]
    ids = {e["node"]["id"] for e in edges}
    assert ids == {graphene.Node.to_global_id("GiftCard", gift_card.pk)}
    assert (
        graphene.Node.to_global_id("GiftCard", gift_card_created_by_staff.pk) not in ids
    )


def test_filter_by_assigned_to_does_not_require_manage_users(
    staff_api_client, gift_card, customer_user, permission_manage_gift_card
):
    # given a requester with MANAGE_GIFT_CARD but not MANAGE_USERS
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])
    variables = {
        "filter": {"assignedTo": [graphene.Node.to_global_id("User", customer_user.pk)]}
    }

    # when
    response = staff_api_client.post_graphql(
        FILTER_QUERY, variables, permissions=[permission_manage_gift_card]
    )

    # then filtering succeeds without MANAGE_USERS (see filter_assigned_to comment)
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" not in content
    edges = content["data"]["giftCards"]["edges"]
    ids = {e["node"]["id"] for e in edges}
    assert graphene.Node.to_global_id("GiftCard", gift_card.pk) in ids
