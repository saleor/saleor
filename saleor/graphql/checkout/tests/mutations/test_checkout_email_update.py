from .....checkout.error_codes import CheckoutErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

CHECKOUT_EMAIL_UPDATE_MUTATION = """
    mutation checkoutEmailUpdate($id: ID, $email: String!) {
        checkoutEmailUpdate(id: $id, email: $email) {
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


def test_checkout_email_update(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    checkout.email = None
    checkout.save(update_fields=["email"])
    previous_last_change = checkout.last_change

    email = "test@example.com"
    variables = {"id": to_global_id_or_none(checkout), "email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.email == email
    assert checkout.last_change != previous_last_change


def test_checkout_email_update_validation(user_api_client, checkout_with_item):
    variables = {"id": to_global_id_or_none(checkout_with_item), "email": ""}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    previous_last_change = checkout_with_item.last_change

    errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "This field cannot be blank."

    checkout_errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert checkout_with_item.last_change == previous_last_change
