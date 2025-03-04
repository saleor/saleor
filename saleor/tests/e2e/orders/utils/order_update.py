from ...account.utils.fragments import ADDRESS_FRAGMENT
from ...utils import get_graphql_content

ORDER_UPDATE_MUTATION = (
    """
    mutation orderUpdate(
        $id: ID
        $externalReference: String
        $input: OrderUpdateInput!
    ) {
        orderUpdate(
            id: $id
            externalReference: $externalReference
            input: $input
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
                externalReference
                shippingAddress {
                    ...Address
                }
                billingAddress {
                    ...Address
                }
            }
        }
    }
"""
    + ADDRESS_FRAGMENT
)


def raw_order_update(api_client, id, input):
    variables = {"id": id, "input": input}

    response = api_client.post_graphql(
        ORDER_UPDATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderUpdate"]

    return data


def order_update(api_client, id, input):
    response = raw_order_update(api_client, id, input)

    assert response["order"] is not None

    errors = response["errors"]

    assert errors == []

    return response
