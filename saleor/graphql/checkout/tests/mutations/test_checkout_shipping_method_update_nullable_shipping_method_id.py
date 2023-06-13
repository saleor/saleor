from unittest.mock import patch

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
                shippingMethod {
                    id
                }
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_shipping_method_update_nullable_shipping_method_id(
    mock_clean_delivery_method,
    staff_api_client,
    checkout_with_item_and_shipping_method,
    count_queries,
):
    # Set up the initial state of the checkout
    checkout = checkout_with_item_and_shipping_method

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

    # Ensure that the clean_delivery_method function was not called
    mock_clean_delivery_method.assert_not_called()
