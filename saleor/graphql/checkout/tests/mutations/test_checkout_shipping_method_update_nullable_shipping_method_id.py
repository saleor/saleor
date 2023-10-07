from unittest.mock import patch

import graphene
import pytest

from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_UPDATE_SHIPPING_METHOD = """
    mutation checkoutShippingMethodUpdate(
        $id: ID, $shippingMethodId: ID
    ) {
        checkoutShippingMethodUpdate(
            id: $id, shippingMethodId: $shippingMethodId
        ) {
            errors {
                field
                message
                code
            }
            checkout {
                id
                token
                voucherCode
                shippingMethod {
                    id
                }
                shippingPrice {
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


@pytest.mark.django_db
@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_shipping_method_update_nullable_shipping_method_id(
    mock_clean_delivery_method,
    staff_api_client,
    shipping_method,
    checkout_with_item_and_voucher_and_shipping_method,
):
    # Set up the initial state of the checkout
    checkout = checkout_with_item_and_voucher_and_shipping_method

    # Mock the clean_delivery_method function
    mock_clean_delivery_method.return_value = True

    # Execute the mutation to remove the shipping method from the checkout
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(checkout), "shippingMethodId": None},
    )

    # Assert that the mutation was successful
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["shippingMethod"] is None

    # Ensure the shipping method was removed from the checkout
    checkout.refresh_from_db(fields=["shipping_method"])
    assert checkout.shipping_method is None

    # Assert that the shipping price is cleared
    assert checkout.shipping_price.net.amount == 0
    assert checkout.shipping_price.gross.amount == 0

    # Assert that the voucher is still assigned to the checkout
    assert checkout.voucher_code is not None

    # Add the shipping method back to the checkout
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        variables={
            "id": to_global_id_or_none(checkout),
            "shippingMethodId": graphene.Node.to_global_id(
                "ShippingMethod", shipping_method.pk
            ),
        },
    )

    # Assert that the mutation was successful
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    errors = data["errors"]
    assert not errors

    # Ensure the shipping method was added back to the checkout
    checkout.refresh_from_db(fields=["shipping_method"])
    assert checkout.shipping_method is not None
