import graphene

from .....account.models import User
from .....checkout.error_codes import CheckoutErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_CHECKOUT_CUSTOMER_ATTACH = """
    mutation checkoutCustomerAttach($id: ID, $customerId: ID) {
        checkoutCustomerAttach(id: $id, customerId: $customerId) {
            checkout {
                token
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_checkout_customer_attach(
    user_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_no_customer_id(
    api_client, user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should fail for unauthenticated customers
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # Mutation should succeed for authenticated customer
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_by_app(
    app_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_by_app_no_customer_id(
    app_api_client, checkout_with_item, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_impersonate_user],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert data["errors"][0]["field"] == "customerId"


def test_checkout_customer_attach_by_app_without_permission(
    app_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query,
        variables,
    )

    assert_no_permission(response)


def test_checkout_customer_attach_user_to_checkout_with_user(
    user_api_client, customer_user, user_checkout, address
):
    checkout = user_checkout

    query = """
    mutation checkoutCustomerAttach($id: ID) {
        checkoutCustomerAttach(id: $id) {
            checkout {
                token
            }
            errors {
                field
                message
                code
            }
        }
    }
"""

    default_address = address.get_copy()
    second_user = User.objects.create_user(
        "test2@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Test2",
        last_name="Tested",
    )

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    customer_id = graphene.Node.to_global_id("User", second_user.pk)
    variables = {"id": checkout_id, "customerId": customer_id}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)
