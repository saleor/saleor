import graphene

from .....checkout.error_codes import CheckoutErrorCode
from ....tests.utils import get_graphql_content

CHECKOUT_EMAIL_UPDATE_MUTATION = """
    mutation checkoutEmailUpdate($checkoutId: ID, $token: UUID, $email: String!) {
        checkoutEmailUpdate(checkoutId: $checkoutId, token: $token, email: $email) {
            checkout {
                id,
                email
            },
            errors {
                field,
                message
            }
            errors {
                field,
                message
                code
            }
        }
    }
"""


def test_checkout_email_update_by_id(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    email = "test@example.com"
    variables = {"checkoutId": checkout_id, "email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.email == email


def test_checkout_email_update_by_token(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])

    email = "test@example.com"
    variables = {"token": checkout.token, "email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.email == email


def test_checkout_email_update_neither_token_and_id_given(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])

    email = "test@example.com"
    variables = {"email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_email_update_both_token_and_id_given(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    email = "test@example.com"

    variables = {"checkoutId": checkout_id, "token": checkout.token, "email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
