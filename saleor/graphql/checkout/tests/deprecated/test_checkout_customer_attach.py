import graphene

from .....checkout.error_codes import CheckoutErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

CHECKOUT_CUSTOMER_ATTACH_MUTATION = """
    mutation checkoutCustomerAttach($checkoutId: ID, $token: UUID) {
        checkoutCustomerAttach(checkoutId: $checkoutId, token: $token) {
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


def test_checkout_customer_attach_by_id(
    api_client, user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = CHECKOUT_CUSTOMER_ATTACH_MUTATION
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"checkoutId": checkout_id, "customerId": customer_id}

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


def test_checkout_customer_attach_by_token(
    api_client, user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = CHECKOUT_CUSTOMER_ATTACH_MUTATION
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"token": checkout.token, "customerId": customer_id}

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


def test_checkout_customer_attach_neither_token_and_id_given(
    user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = CHECKOUT_CUSTOMER_ATTACH_MUTATION
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_customer_attach_both_token_and_id_given(
    user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = CHECKOUT_CUSTOMER_ATTACH_MUTATION
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {
        "checkoutId": checkout_id,
        "token": checkout.token,
        "customerId": customer_id,
    }

    # Mutation should succeed for authenticated customer
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
