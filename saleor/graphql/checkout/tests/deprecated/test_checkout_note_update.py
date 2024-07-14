import graphene

from .....checkout.error_codes import CheckoutErrorCode
from ....tests.utils import get_graphql_content

CHECKOUT_NOTE_UPDATE_MUTATION = """
    mutation checkoutNoteUpdate($checkoutId: ID, $token: UUID, $note: String!) {
        checkoutNoteUpdate(checkoutId: $checkoutId, token: $token, note: $note) {
            checkout {
                id,
                note
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


def test_checkout_note_update_by_id(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    checkout.note = ""
    checkout.save(update_fields=["note"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    note = "New note value"
    variables = {"checkoutId": checkout_id, "note": note}

    response = user_api_client.post_graphql(CHECKOUT_NOTE_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutNoteUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.note == note


def test_checkout_note_update_by_token(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    checkout.note = ""
    checkout.save(update_fields=["note"])

    note = "New note value"
    variables = {"token": checkout.token, "note": note}

    response = user_api_client.post_graphql(CHECKOUT_NOTE_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutNoteUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.note == note


def test_checkout_note_update_neither_token_and_id_given(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    checkout.note = ""
    checkout.save(update_fields=["note"])

    note = "New note value"
    variables = {"note": note}

    response = user_api_client.post_graphql(CHECKOUT_NOTE_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutNoteUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_note_update_both_token_and_id_given(
    user_api_client, checkout_with_item
):
    checkout = checkout_with_item
    checkout.note = ""
    checkout.save(update_fields=["note"])

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    note = "New note value"

    variables = {"checkoutId": checkout_id, "token": checkout.token, "note": note}

    response = user_api_client.post_graphql(CHECKOUT_NOTE_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutNoteUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
