from .....account.models import User
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_CHECKOUT_CUSTOMER_DETACH = """
    mutation checkoutCustomerDetach($id: ID) {
        checkoutCustomerDetach(id: $id) {
            checkout {
                token
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_checkout_customer_detach(user_api_client, checkout_with_item, customer_user):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    previous_last_change = checkout.last_change

    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed if the user owns this checkout.
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerDetach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user is None
    assert checkout.last_change != previous_last_change

    # Mutation should fail when user calling it doesn't own the checkout.
    other_user = User.objects.create_user("othercustomer@example.com", "password")
    checkout.user = other_user
    checkout.save()
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables
    )
    assert_no_permission(response)


def test_checkout_customer_detach_by_app(
    app_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    previous_last_change = checkout.last_change

    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed if the user owns this checkout.
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH,
        variables,
        permissions=[permission_impersonate_user],
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerDetach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user is None
    assert checkout.last_change != previous_last_change


def test_checkout_customer_detach_by_app_without_permissions(
    app_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    previous_last_change = checkout.last_change

    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed if the user owns this checkout.
    response = app_api_client.post_graphql(MUTATION_CHECKOUT_CUSTOMER_DETACH, variables)

    assert_no_permission(response)
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change
