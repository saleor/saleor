import graphene
import pytest

from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.models import Checkout
from .....payment.models import TransactionItem
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_CHECKOUT_DELETE = """
    mutation checkoutDelete($id: ID!) {
        checkoutDelete(id: $id) {
            errors {
                message
                code
                field
            }
        }
    }
"""


def test_checkout_delete_by_staff(
    staff_api_client, checkout_with_items, permission_manage_checkouts
):
    # given
    checkout = checkout_with_items
    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CHECKOUT_DELETE,
        variables,
        permissions=[permission_manage_checkouts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutDelete"]
    assert data["errors"] == []
    assert not Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_delete_by_app(
    app_api_client, checkout_with_items, permission_manage_checkouts
):
    # given
    checkout = checkout_with_items
    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id}

    # when
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_DELETE,
        variables,
        permissions=[permission_manage_checkouts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutDelete"]
    assert data["errors"] == []
    assert not Checkout.objects.filter(pk=checkout.pk).exists()


@pytest.mark.parametrize("client", ["api_client", "user_api_client"])
def test_checkout_delete_without_permission_is_denied(
    client, request, checkout_with_items
):
    # given
    api_client = request.getfixturevalue(client)
    checkout = checkout_with_items
    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id}

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_DELETE, variables)

    # then
    assert_no_permission(response)
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_delete_by_staff_without_permission_is_denied(
    staff_api_client, checkout_with_items
):
    # given
    checkout = checkout_with_items
    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id}

    # when
    response = staff_api_client.post_graphql(MUTATION_CHECKOUT_DELETE, variables)

    # then
    assert_no_permission(response)
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_delete_by_app_without_permission_is_denied(
    app_api_client, checkout_with_items
):
    # given
    checkout = checkout_with_items
    checkout_id = to_global_id_or_none(checkout)
    variables = {"id": checkout_id}

    # when
    response = app_api_client.post_graphql(MUTATION_CHECKOUT_DELETE, variables)

    # then
    assert_no_permission(response)
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_delete_invalid_checkout_id(
    staff_api_client, checkout_with_items, permission_manage_checkouts
):
    # given
    checkout = checkout_with_items
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    checkout.delete()
    variables = {"id": checkout_id}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CHECKOUT_DELETE,
        variables,
        permissions=[permission_manage_checkouts],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["checkoutDelete"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert errors[0]["message"] == f"Couldn't resolve to a node: {checkout_id}"


def test_checkout_delete_with_id_of_different_type(
    staff_api_client,
    checkout_with_items,
    customer_user,
    permission_manage_checkouts,
):
    # given
    checkout = checkout_with_items
    fake_checkout_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": fake_checkout_id}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CHECKOUT_DELETE,
        variables,
        permissions=[permission_manage_checkouts],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["checkoutDelete"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["message"] == (
        f"Invalid ID: {fake_checkout_id}. Expected: Checkout, received: User."
    )
    assert Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_delete_with_attached_transaction(
    staff_api_client,
    checkout_with_items,
    permission_manage_checkouts,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_items
    checkout_id = to_global_id_or_none(checkout)
    transaction = transaction_item_generator(checkout_id=checkout.pk)
    variables = {"id": checkout_id}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CHECKOUT_DELETE,
        variables,
        permissions=[permission_manage_checkouts],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["checkoutDelete"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == CheckoutErrorCode.INVALID.name
    assert errors[0]["message"] == "Cannot delete checkout with attached transactions."
    assert Checkout.objects.filter(pk=checkout.pk).exists()
    assert TransactionItem.objects.filter(pk=transaction.pk).exists()
