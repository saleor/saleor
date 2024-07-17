from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

CHECKOUT_NOTE_UPDATE_MUTATION = """
    mutation checkoutNoteUpdate($id: ID, $note: String!) {
        checkoutNoteUpdate(id: $id, note: $note) {
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


def test_checkout_note_update(user_api_client, checkout_with_item):
    # given
    checkout = checkout_with_item
    checkout.note = ""
    checkout.save(update_fields=["note"])
    previous_last_change = checkout.last_change

    note = "New note value"
    variables = {"id": to_global_id_or_none(checkout), "note": note}

    # when
    response = user_api_client.post_graphql(CHECKOUT_NOTE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutNoteUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.note == note
    assert checkout.last_change != previous_last_change


def test_with_active_problems_flow(api_client, checkout_with_problems):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "note": "New note value",
    }

    # when
    response = api_client.post_graphql(
        CHECKOUT_NOTE_UPDATE_MUTATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutNoteUpdate"]["errors"]
