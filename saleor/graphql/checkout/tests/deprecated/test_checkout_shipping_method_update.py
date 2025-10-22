import graphene

from .....checkout.error_codes import CheckoutErrorCode
from ....tests.utils import get_graphql_content

MUTATION_UPDATE_SHIPPING_METHOD = """
    mutation checkoutShippingMethodUpdate(
            $checkoutId: ID, $token: UUID, $shippingMethodId: ID!){
        checkoutShippingMethodUpdate(
            checkoutId: $checkoutId,
            token: $token,
            shippingMethodId: $shippingMethodId
        ) {
            errors {
                field
                message
                code
            }
            checkout {
                id
                token
            }
        }
    }
"""


def test_checkout_shipping_method_update_by_id(
    staff_api_client,
    shipping_method,
    checkout_with_item_and_shipping_method,
):
    # given
    checkout = checkout_with_item_and_shipping_method
    query = MUTATION_UPDATE_SHIPPING_METHOD

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query, {"checkoutId": checkout_id, "shippingMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert data["checkout"]["id"] == checkout_id
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)


def test_checkout_shipping_method_update_by_token(
    staff_api_client,
    shipping_method,
    checkout_with_item_and_shipping_method,
):
    checkout = checkout_with_item_and_shipping_method
    query = MUTATION_UPDATE_SHIPPING_METHOD

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"token": checkout.token, "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert data["checkout"]["id"] == checkout_id
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)


def test_checkout_shipping_method_update_neither_token_and_id_given(
    staff_api_client, checkout_with_item, shipping_method
):
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(query, {"shippingMethodId": method_id})
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_shipping_method_update_both_token_and_id_given(
    staff_api_client, checkout_with_item, shipping_method
):
    checkout = checkout_with_item
    query = MUTATION_UPDATE_SHIPPING_METHOD

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {
            "checkoutId": checkout_id,
            "token": checkout_with_item.token,
            "shippingMethodId": method_id,
        },
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    assert len(data["errors"]) == 1
    assert not data["checkout"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_shipping_method_update_by_id_no_checkout_metadata(
    staff_api_client,
    shipping_method,
    checkout_with_item_and_shipping_method,
):
    # given
    checkout = checkout_with_item_and_shipping_method
    query = MUTATION_UPDATE_SHIPPING_METHOD

    checkout.metadata_storage.delete()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query, {"checkoutId": checkout_id, "shippingMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert data["checkout"]["id"] == checkout_id
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)
